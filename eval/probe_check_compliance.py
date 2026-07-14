"""
Phase 4 prep — NOT the formal 30-case regression set yet. This is a smaller,
deliberately varied probe (clear-compliant / clear-non-compliant / ambiguous /
cross-document) run against the REAL pipeline (real Qdrant data, real Groq
calls) so we can see actual failure modes before designing the formal
regression harness around them, instead of guessing what might go wrong.

Run from mcp_server/: python ../eval/probe_check_compliance.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))

import tools  # noqa: E402

PROBE_CASES = [
    # --- Expected: clearly Compliant ---
    {
        "label": "clear_compliant_1",
        "policy": "We retain customer KYC identification records for five years after the account relationship ends.",
        "expected_direction": "Compliant",
    },
    {
        "label": "clear_compliant_2",
        "policy": "We do not charge any pre-payment penalty when a microfinance borrower repays their loan early.",
        "expected_direction": "Compliant",
    },

    # --- Expected: clearly Non-Compliant ---
    {
        "label": "clear_noncompliant_1",
        "policy": "We open savings accounts for customers who want to use a made-up name instead of their real identity.",
        "expected_direction": "Non-Compliant",
    },
    {
        "label": "clear_noncompliant_2",
        "policy": "We link a microfinance loan to a lien on the borrower's savings account as collateral.",
        "expected_direction": "Non-Compliant",
    },
    {
        "label": "clear_noncompliant_3",
        "policy": "Our recovery agents call defaulting microfinance borrowers at 5:30 a.m. to press for payment.",
        "expected_direction": "Non-Compliant",
    },

    # --- Deliberately ambiguous / partial match ---
    {
        "label": "ambiguous_1",
        "policy": "We increase a microfinance borrower's effective rate mid-term by adding a new processing fee, without prior notice, because our funding costs rose.",
        "expected_direction": "ambiguous — touches both 'prospective only' and 'usurious/disclosure' rules, could be Non-Compliant OR flagged for multiple reasons",
    },
    {
        "label": "ambiguous_2",
        "policy": "We classify a customer as low-risk for KYC purposes based solely on their income level, without considering any other factors.",
        "expected_direction": "ambiguous — policy doesn't fully specify all required risk factors, tests whether the model over- or under-claims compliance",
    },
    {
        "label": "ambiguous_3",
        "policy": "We want to offer a slightly discounted interest rate to employees who refer new personal loan customers to us.",
        "expected_direction": "ambiguous — not directly addressed by any single clause, tests empty/weak-match handling",
    },

    # --- Cross-document / topic overlap (tests document confusion from Phase 2) ---
    {
        "label": "cross_doc_1",
        "policy": "We change the interest rate on an existing floating-rate personal loan and apply the new rate retroactively to instalments already due.",
        "expected_direction": "Non-Compliant — relevant clause could plausibly live in EITHER rbi_interest_rate_advances or rbi_microfinance_fair_practices depending on loan type; tests whether retrieval picks a sensible one",
    },
    {
        "label": "cross_doc_2",
        "policy": "We outsource our loan recovery process to a third-party agency and take the position that any mishandling is the agency's liability, not ours.",
        "expected_direction": "Non-Compliant — this was a known Phase 2 retrieval miss (clause 7.3.1), worth re-checking now that reranking is wired in",
    },

    # --- Nonsense / out-of-corpus (tests graceful empty-match handling) ---
    {
        "label": "out_of_corpus",
        "policy": "We want to launch a new cryptocurrency staking product for retail customers.",
        "expected_direction": "not covered by current corpus — should gracefully return Requires Legal Review, not fabricate a verdict",
    },
]


def run_probe():
    results = []
    for case in PROBE_CASES:
        print(f"\n{'=' * 70}\n[{case['label']}]")
        print(f"Policy: {case['policy']}")
        print(f"Expected direction: {case['expected_direction']}")

        result = tools.check_compliance(case["policy"])

        print(f"\n--- ACTUAL RESULT ---")
        print(f"Verdict: {result.get('verdict')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Grounding verified: {result.get('grounding_verified')}")
        print(f"Source clause: {result.get('source_clause')}")
        print(f"Evidence quote: {result.get('evidence_quote', '')[:200]}")
        print(f"Reasoning: {result.get('reasoning', '')[:300]}")

        results.append({"case": case, "result": result})

    # Save full raw output for review, since terminal scrollback is lossy
    output_path = Path(__file__).resolve().parent / "probe_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n\nFull results saved to {output_path}")

    # Quick summary flags — not a pass/fail grade, just things worth a human look
    print(f"\n{'=' * 70}\nFLAGS WORTH REVIEWING:")
    for r in results:
        result = r["result"]
        if not result.get("grounding_verified", True) and "error" not in result:
            print(f"  - [{r['case']['label']}] grounding_verified=False — check if this is a "
                  f"correct catch (hallucination) or a false alarm (real quote, formatting mismatch)")
        if result.get("confidence", 1.0) > 0.9 and result.get("verdict") not in \
                ("Compliant", "Non-Compliant"):
            print(f"  - [{r['case']['label']}] high confidence but non-definitive verdict — worth a look")


if __name__ == "__main__":
    run_probe()
