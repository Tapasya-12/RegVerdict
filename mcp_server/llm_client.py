"""
Groq-based replacement for claude_client.py — same generate_verdict()
interface (policy_text + retrieved_chunks -> VerdictOutput, top_chunk), so
tools.py only needs one import line changed. Swapped to Groq for its free
tier; Groq's Python SDK follows the same chat-completions message shape as
OpenAI, so this looks structurally similar to the Anthropic version.

Model: llama-3.3-70b-versatile — good general reasoning quality, and Groq
supports native JSON mode (response_format={"type": "json_object"}) on this
model, which is more reliable than asking nicely in the prompt and hoping.
"""

import json
import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

from schema import VerdictOutput

# Explicit path, not a bare load_dotenv() — this module gets imported via a
# sys.path.insert() from tools.py, often with a cwd that isn't mcp_server/
# (e.g. eval/test_mcp_contracts.py runs from eval/), and dotenv's implicit
# discovery doesn't reliably walk back to this file's own directory in that
# case. Anchoring to __file__ makes it work regardless of caller cwd.
load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL_NAME = "llama-3.3-70b-versatile"
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VERDICT_SYSTEM_PROMPT = """You are a regulatory compliance analyst. You will be given a business \
policy statement and one or more retrieved regulatory clauses. Your job is to determine whether \
the policy complies with the clause(s).

CRITICAL RULES:
1. Your evidence_quote MUST be copied VERBATIM (character-for-character) from the provided \
clause text. Do not paraphrase it, summarize it, or combine text from multiple places. If you \
cannot find a verbatim span that supports your verdict, say so honestly in reasoning and lower \
your confidence — do not fabricate a quote to fit your conclusion.
2. confidence must reflect genuine uncertainty. If the clause is ambiguous, doesn't fully cover \
the policy scenario, or requires judgment calls a human should make, use a LOW confidence score \
and prefer "Requires Legal Review" over guessing Compliant/Non-Compliant.
3. Respond with ONLY a JSON object matching this exact shape, nothing else — no markdown fences, \
no preamble:
{
  "policy_summary": "one-line restatement of the submitted policy",
  "verdict": "Compliant" | "Non-Compliant" | "Requires Legal Review",
  "confidence": 0.0-1.0,
  "evidence_quote": "verbatim span from the clause text provided",
  "reasoning": "plain-English explanation grounded in evidence_quote",
  "recommended_action": "next step: modify policy / file for approval / consult legal / no action needed"
}
"""


def generate_verdict(policy_text: str, retrieved_chunks: list[dict]) -> tuple[VerdictOutput, dict]:
    """
    retrieved_chunks: output of HybridRetriever.retrieve_with_rerank() — each
    dict has 'text', 'document_name', 'clause_number', 'effective_date', etc.

    Returns (VerdictOutput, top_chunk) — top_chunk is returned separately so
    the caller can pass its raw text to grounding.apply_grounding_check()
    without re-deriving which chunk the model was actually shown as primary.
    """
    if not retrieved_chunks:
        raise ValueError("generate_verdict called with no retrieved chunks — caller should "
                          "handle the empty-corpus-match case before calling this.")

    top_chunk = retrieved_chunks[0]

    clauses_block = "\n\n".join(
        f"[Clause {c.get('clause_number')} — {c.get('document_name')}]\n{c.get('text', '')}"
        for c in retrieved_chunks
    )

    user_message = (
        f"POLICY STATEMENT:\n{policy_text}\n\n"
        f"RETRIEVED REGULATORY CLAUSES:\n{clauses_block}\n\n"
        f"Evaluate the policy statement against these clauses and respond with the JSON object "
        f"described in your instructions."
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": VERDICT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    raw_text = response.choices[0].message.content.strip()
    # Defensive strip even with JSON mode on — belt and suspenders
    raw_text = raw_text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {raw_text[:300]}") from e

    verdict_output = VerdictOutput(
        policy_summary=parsed["policy_summary"],
        verdict=parsed["verdict"],
        confidence=float(parsed["confidence"]),
        evidence_quote=parsed["evidence_quote"],
        source_clause={
            "document": top_chunk.get("document_name", ""),
            "clause_number": top_chunk.get("clause_number", ""),
            "effective_date": top_chunk.get("effective_date", ""),
        },
        reasoning=parsed["reasoning"],
        recommended_action=parsed["recommended_action"],
    )

    return verdict_output, top_chunk
