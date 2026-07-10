"""
Post-hoc grounding check, per design doc's "Evidence-verified" differentiator
and the roadmap's #1 listed risk: "Hallucinated citations — force the LLM to
quote the retrieved chunk verbatim, then verify the quoted span exists in the
source chunk before rendering; flag mismatches as 'Requires Legal Review'."

This is deliberately dumb and mechanical — a substring/fuzzy match, not
another LLM call — because the whole point is to have ONE thing in the
pipeline that isn't trusting the model's own claim about itself.
"""

import re
from schema import VerdictOutput, CONFIDENCE_DOWNGRADE_THRESHOLD, Verdict


def _normalize(text: str) -> str:
    """Collapse whitespace and lowercase, so a quote isn't rejected just
    because the model reflowed line breaks or added/dropped a double space
    when copying it out."""
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_evidence_quote(evidence_quote: str, source_chunk_text: str) -> bool:
    """
    Returns True if evidence_quote appears verbatim (whitespace-normalized)
    inside source_chunk_text. This is intentionally strict — a paraphrase
    should NOT pass, since a paraphrase is exactly what could hide a
    hallucinated or distorted claim.
    """
    if not evidence_quote or not source_chunk_text:
        return False
    return _normalize(evidence_quote) in _normalize(source_chunk_text)


def apply_grounding_check(verdict_output: VerdictOutput, source_chunk_text: str) -> VerdictOutput:
    """
    Mutates verdict_output in place (returns it too, for chaining):
    - Sets grounding_verified / grounding_note.
    - Auto-downgrades to REQUIRES_LEGAL_REVIEW if the quote can't be verified
      OR if confidence is below the threshold — per the roadmap's explicit
      mitigation for hallucinated citations and low-confidence verdicts.
    """
    is_grounded = verify_evidence_quote(verdict_output.evidence_quote, source_chunk_text)
    verdict_output.grounding_verified = is_grounded

    if not is_grounded:
        verdict_output.grounding_note = (
            "Evidence quote could not be verified against the retrieved source "
            "chunk verbatim. Auto-downgraded — do not trust this verdict without "
            "manual review of the source clause."
        )
        verdict_output.verdict = Verdict.REQUIRES_LEGAL_REVIEW
        verdict_output.confidence = min(verdict_output.confidence, 0.5)
        return verdict_output

    if verdict_output.confidence < CONFIDENCE_DOWNGRADE_THRESHOLD and \
            verdict_output.verdict in (Verdict.COMPLIANT, Verdict.NON_COMPLIANT):
        verdict_output.grounding_note = (
            f"Confidence {verdict_output.confidence:.2f} is below the "
            f"{CONFIDENCE_DOWNGRADE_THRESHOLD} auto-downgrade threshold."
        )
        verdict_output.verdict = Verdict.REQUIRES_LEGAL_REVIEW
        return verdict_output

    verdict_output.grounding_note = "Evidence quote verified verbatim against source chunk."
    return verdict_output
