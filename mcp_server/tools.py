"""
Implementation of the 7 MCP tools per design doc section 3. Each function
here is plain Python — server.py wraps them as MCP tools. Kept separate so
these are testable without spinning up an MCP server/client at all.

Known simplification (flagged honestly, not hidden): compare_jurisdictions
and detect_regulatory_conflicts filter regulator-specific results out of a
shared top-20 hybrid-retrieval candidate pool, rather than running a fully
independent per-regulator search. Fine for the current 3-document corpus;
worth revisiting once SEZ/GDPR are added as genuinely separate regulators
in Phase 6, per the design doc's own multi-regulator stretch goal.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))

from retriever import HybridRetriever  # noqa: E402
from schema import VerdictOutput, Verdict, SourceClause  # noqa: E402
from grounding import apply_grounding_check  # noqa: E402
from llm_client import generate_verdict  # noqa: E402

# Retriever is expensive to construct (loads embedding model + builds BM25
# index) — build once, reuse across all tool calls in this process.
_retriever_singleton: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _retriever_singleton
    if _retriever_singleton is None:
        _retriever_singleton = HybridRetriever()
    return _retriever_singleton


# ---------------------------------------------------------------------------
# Tool 1: fetch_regulation(topic) — baseline retrieval, no verdict
# ---------------------------------------------------------------------------

def fetch_regulation(topic: str, top_k: int = 5) -> dict:
    if not topic or not topic.strip():
        return {"error": "topic must be a non-empty string", "results": []}

    retriever = get_retriever()
    chunks = retriever.retrieve_with_rerank(topic, top_k=top_k)

    if not chunks:
        return {
            "topic": topic,
            "results": [],
            "note": "No matching regulatory clauses found in the indexed corpus.",
        }

    return {
        "topic": topic,
        "results": [
            {
                "document_name": c.get("document_name"),
                "clause_number": c.get("clause_number"),
                "regulator": c.get("regulator"),
                "effective_date": c.get("effective_date"),
                "text": c.get("text"),
            }
            for c in chunks
        ],
    }


# ---------------------------------------------------------------------------
# Tool 2: check_compliance(policy_text) — the core verdict tool
# ---------------------------------------------------------------------------

def check_compliance(policy_text: str) -> dict:
    if not policy_text or not policy_text.strip():
        return {"error": "policy_text must be a non-empty string"}

    retriever = get_retriever()
    chunks = retriever.retrieve_with_rerank(policy_text, top_k=5)

    if not chunks:
        # Empty-corpus-match case — must not silently fabricate a verdict.
        return {
            "policy_summary": policy_text[:200],
            "verdict": Verdict.REQUIRES_LEGAL_REVIEW.value,
            "confidence": 0.0,
            "evidence_quote": "",
            "source_clause": None,
            "reasoning": "No relevant regulatory clauses were found in the indexed corpus "
                         "for this policy statement. A verdict cannot be grounded — this "
                         "requires manual legal review.",
            "recommended_action": "Consult legal / verify whether relevant regulation exists "
                                   "outside the current indexed corpus.",
            "grounding_verified": False,
        }

    verdict_output = generate_verdict(policy_text, chunks)
    apply_grounding_check(verdict_output, chunks)

    return verdict_output.model_dump()


# ---------------------------------------------------------------------------
# Tool 3: generate_compliance_report(policy_text) — check_compliance,
# extended with the full retrieved-clause list (not just the top one used
# for the verdict), for the report's "relevant regulations found" section.
# ---------------------------------------------------------------------------

def generate_compliance_report(policy_text: str) -> dict:
    if not policy_text or not policy_text.strip():
        return {"error": "policy_text must be a non-empty string"}

    retriever = get_retriever()
    chunks = retriever.retrieve_with_rerank(policy_text, top_k=5)

    verdict_result = check_compliance(policy_text)  # reuses the same grounded verdict

    return {
        "policy_received": policy_text,
        "relevant_regulations_found": [
            {
                "document_name": c.get("document_name"),
                "clause_number": c.get("clause_number"),
                "regulator": c.get("regulator"),
            }
            for c in chunks[:3]  # top 2-3 per design doc's output layer spec
        ],
        "verdict": verdict_result,
    }


# ---------------------------------------------------------------------------
# Tool 4: compare_jurisdictions(policy_text, regulators)
# ---------------------------------------------------------------------------

def compare_jurisdictions(policy_text: str, regulators: list[str]) -> dict:
    if not policy_text or not policy_text.strip():
        return {"error": "policy_text must be a non-empty string"}
    if not regulators:
        return {"error": "regulators must be a non-empty list"}

    retriever = get_retriever()
    # Wider pool since we're about to filter it down per regulator
    candidate_pool = retriever.retrieve(policy_text, top_k=20)

    results = {}
    for regulator in regulators:
        regulator_chunks = [c for c in candidate_pool if c.get("regulator") == regulator][:5]

        if not regulator_chunks:
            results[regulator] = {
                "verdict": Verdict.REQUIRES_LEGAL_REVIEW.value,
                "reasoning": f"No indexed clauses found for regulator '{regulator}' relevant "
                             f"to this policy. Either this regulator's corpus is thin/absent, "
                             f"or this policy area isn't covered by {regulator} regulation.",
                "confidence": 0.0,
            }
            continue

        verdict_output = generate_verdict(policy_text, regulator_chunks)
        apply_grounding_check(verdict_output, regulator_chunks)
        results[regulator] = verdict_output.model_dump()

    return {"policy_text": policy_text, "results_by_regulator": results}


# ---------------------------------------------------------------------------
# Tool 5: detect_regulatory_conflicts(policy_text)
# ---------------------------------------------------------------------------

def detect_regulatory_conflicts(policy_text: str) -> dict:
    if not policy_text or not policy_text.strip():
        return {"error": "policy_text must be a non-empty string"}

    retriever = get_retriever()
    candidate_pool = retriever.retrieve(policy_text, top_k=20)

    regulators_present = sorted({c.get("regulator") for c in candidate_pool if c.get("regulator")})

    if len(regulators_present) < 2:
        return {
            "policy_text": policy_text,
            "conflict_detected": False,
            "note": f"Only one regulator ({regulators_present[0] if regulators_present else 'none'}) "
                    f"has relevant indexed clauses — no cross-regulator conflict is possible to detect "
                    f"with the current corpus.",
        }

    comparison = compare_jurisdictions(policy_text, regulators_present)
    verdicts_seen = {
        reg: result.get("verdict")
        for reg, result in comparison["results_by_regulator"].items()
        if "verdict" in result
    }
    distinct_verdicts = set(verdicts_seen.values())
    non_review_verdicts = distinct_verdicts - {"Requires Legal Review"}
    conflict_detected = len(non_review_verdicts) > 1

    return {
        "policy_text": policy_text,
        "regulators_compared": regulators_present,
        "verdicts_by_regulator": verdicts_seen,
        "conflict_detected": conflict_detected,
        "verdict": Verdict.CONFLICTING_REGULATIONS.value if conflict_detected else None,
        "detail": comparison["results_by_regulator"],
    }


# ---------------------------------------------------------------------------
# Tool 6: get_regulation_history(clause_id)
# ---------------------------------------------------------------------------

def get_regulation_history(clause_id: str) -> dict:
    if not clause_id or not clause_id.strip():
        return {"error": "clause_id must be a non-empty string"}

    retriever = get_retriever()
    # clause_id may be a full composite chunk_id or just a bare clause_number —
    # search payloads for either match, since the composite ID scheme
    # (document::parent_section::clause_number[::page][::n]) means callers
    # may not always have the exact full string on hand.
    matches = [
        payload for payload in retriever.payload_by_id.values()
        if payload.get("chunk_id") == clause_id or payload.get("clause_number") == clause_id
    ]

    if not matches:
        return {"clause_id": clause_id, "found": False,
                "note": "No chunk found matching this clause_id or clause_number."}

    results = []
    for payload in matches:
        supersedes = payload.get("supersedes_clause_id", "")
        superseded_by = payload.get("superseded_by_clause_id", "")
        results.append({
            "document_name": payload.get("document_name"),
            "clause_number": payload.get("clause_number"),
            "effective_date": payload.get("effective_date"),
            "supersedes_clause_id": supersedes or None,
            "superseded_by_clause_id": superseded_by or None,
            "has_recorded_history": bool(supersedes or superseded_by),
        })

    return {"clause_id": clause_id, "found": True, "matches": results}


# ---------------------------------------------------------------------------
# Tool 7: simulate_policy_change(original_policy, proposed_change)
# ---------------------------------------------------------------------------

def simulate_policy_change(original_policy: str, proposed_change: str) -> dict:
    if not original_policy or not original_policy.strip():
        return {"error": "original_policy must be a non-empty string"}
    if not proposed_change or not proposed_change.strip():
        return {"error": "proposed_change must be a non-empty string"}

    original_result = check_compliance(original_policy)
    proposed_result = check_compliance(proposed_change)

    status_flipped = original_result.get("verdict") != proposed_result.get("verdict")

    return {
        "original_policy": original_policy,
        "original_verdict": original_result,
        "proposed_change": proposed_change,
        "proposed_verdict": proposed_result,
        "status_flipped": status_flipped,
        "summary": (
            f"Verdict changed from '{original_result.get('verdict')}' to "
            f"'{proposed_result.get('verdict')}'" if status_flipped
            else f"Verdict unchanged: '{original_result.get('verdict')}'"
        ),
    }
