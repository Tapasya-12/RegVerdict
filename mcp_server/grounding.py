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


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tokens_fuzzy_equal(a: str, b: str) -> bool:
    """
    Treats two tokens as equal if identical, OR if one is the other with
    stray digits glued on (the confirmed 'footnote number fused mid-word'
    extraction artifact — e.g. source token '45including' vs quote token
    'including'). Deliberately does NOT strip digits from purely-numeric
    tokens (percentages, clause numbers) — only from alnum tokens that
    contain letters, so a real number like '60' can never fuzzy-match '6'.
    """
    if a == b:
        return True
    a_has_letters = any(c.isalpha() for c in a)
    b_has_letters = any(c.isalpha() for c in b)
    if a_has_letters and b_has_letters:
        a_stripped = re.sub(r"\d+", "", a)
        b_stripped = re.sub(r"\d+", "", b)
        if a_stripped and a_stripped == b_stripped:
            return True
    return False


def _subsequence_match_with_gaps(quote_tokens: list[str], source_tokens: list[str],
                                  max_gap: int = 12) -> bool:
    """
    Returns True if every token in quote_tokens appears in source_tokens, IN
    ORDER, with at most `max_gap` unmatched source tokens between consecutive
    matches. This tolerates exactly the noise pattern seen in this corpus —
    stray characters, glued footnote numbers, a footnote/citation block
    spliced mid-sentence — because those show up as EXTRA tokens interspersed
    between real ones, never as the real words being changed.

    Crucially, this does NOT tolerate a fabricated quote that reuses a few
    common words: every single quote token must still be found, in order,
    within a bounded window — a hallucinated claim with different substantive
    content will fail this just as it fails the strict check.
    """
    if not quote_tokens:
        return False
    search_from = 0
    for q_tok in quote_tokens:
        window_end = min(search_from + max_gap + 1, len(source_tokens))
        match_idx = None
        for j in range(search_from, window_end):
            if _tokens_fuzzy_equal(source_tokens[j], q_tok):
                match_idx = j
                break
        if match_idx is None:
            return False
        search_from = match_idx + 1
    return True


def verify_evidence_quote(evidence_quote: str, source_chunk_text: str) -> tuple[bool, str]:
    """
    Two-tier check:
    1. Strict verbatim (whitespace-normalized) substring match — unchanged
       behavior, the fast/common path for clean source text.
    2. Fallback: noise-tolerant ordered-subsequence match — only reached if
       tier 1 fails, and only passes if the quote is a genuine, short-quote-
       proof match against real corpus noise, not a loose fuzzy match.

    Returns (is_grounded, match_tier) where match_tier is "exact",
    "noise_tolerant", or "none" — callers should surface which tier matched,
    since a noise_tolerant match means "verified, but the source PDF has
    known extraction artifacts here," which is useful information, not
    something to hide behind a plain True/False.
    """
    if not evidence_quote or not source_chunk_text:
        return False, "none"

    if _normalize(evidence_quote) in _normalize(source_chunk_text):
        return True, "exact"

    quote_tokens = _tokenize(evidence_quote)
    source_tokens = _tokenize(source_chunk_text)
    # Require a minimum quote length before trusting the fallback tier at
    # all — a 2-3 word quote could plausibly subsequence-match by chance
    # even in an unrelated chunk, which would defeat the point.
    if len(quote_tokens) >= 5 and _subsequence_match_with_gaps(quote_tokens, source_tokens):
        return True, "noise_tolerant"

    return False, "none"


def find_matching_chunks(evidence_quote: str, chunks: list[dict]) -> list[tuple[dict, str]]:
    """
    Searches ALL retrieved chunks (in rank order) for whichever one(s)
    actually contain evidence_quote — either exactly or via the noise-
    tolerant fallback. Returns [(chunk, match_tier), ...] for every chunk
    that matched, preserving the rank order chunks were passed in.

    This is what fixes the earlier mislabeling bug: source_clause should
    never be blindly attributed to rank-1 — it must be attributed to
    whichever chunk actually backs the quote.
    """
    matches = []
    for chunk in chunks:
        is_grounded, tier = verify_evidence_quote(evidence_quote, chunk.get("text", ""))
        if is_grounded:
            matches.append((chunk, tier))
    return matches


def apply_grounding_check(verdict_output: VerdictOutput, retrieved_chunks: list[dict]) -> VerdictOutput:
    """
    Mutates verdict_output in place (returns it too, for chaining):
    - Finds which retrieved chunk (if any) actually backs the evidence_quote.
    - 1 match -> attribute source_clause + grounding to it.
    - 0 matches -> genuine ungrounded claim; auto-downgrade, fall back to
      rank-1 as the "best guess" source for display purposes.
    - 2+ matches -> attribute to the highest-ranked match, but flag the
      ambiguity explicitly rather than silently picking one.
    - Also applies the confidence auto-downgrade rule independent of
      grounding tier (a noise_tolerant match still counts as grounded for
      this rule — it's a real quote, just against noisy source text).
    """
    if not retrieved_chunks:
        verdict_output.grounding_verified = False
        verdict_output.grounding_note = "No retrieved chunks were provided to ground against."
        verdict_output.verdict = Verdict.REQUIRES_LEGAL_REVIEW
        return verdict_output

    matches = find_matching_chunks(verdict_output.evidence_quote, retrieved_chunks)

    if len(matches) == 0:
        # Genuine ungrounded claim — keep existing downgrade behavior,
        # attributed to rank-1 as a best-guess display source.
        top_chunk = retrieved_chunks[0]
        verdict_output.source_clause = {
            "document": top_chunk.get("document_name", ""),
            "clause_number": top_chunk.get("clause_number", ""),
            "effective_date": top_chunk.get("effective_date", ""),
        }
        verdict_output.grounding_verified = False
        verdict_output.grounding_note = (
            "Evidence quote could not be verified against any retrieved source chunk, "
            "even allowing for known extraction noise. Auto-downgraded — do not trust "
            "this verdict without manual review of the source clause."
        )
        verdict_output.verdict = Verdict.REQUIRES_LEGAL_REVIEW
        verdict_output.confidence = min(verdict_output.confidence, 0.5)
        return verdict_output

    best_chunk, best_tier = matches[0]  # matches preserves rank order -> first is highest-ranked
    verdict_output.source_clause = {
        "document": best_chunk.get("document_name", ""),
        "clause_number": best_chunk.get("clause_number", ""),
        "effective_date": best_chunk.get("effective_date", ""),
    }
    verdict_output.grounding_verified = True

    note_parts = []
    if best_tier == "noise_tolerant":
        note_parts.append(
            "Evidence quote verified against source chunk via noise-tolerant matching — "
            "the source PDF has known extraction artifacts (stray characters/footnote "
            "splices) near this quote, but the quote's content matches in order."
        )
    else:
        note_parts.append("Evidence quote verified verbatim against source chunk.")

    if len(matches) > 1:
        other_docs = [f"{c.get('document_name')}::{c.get('clause_number')}" for c, _ in matches[1:]]
        note_parts.append(
            f"Note: this exact quote also matched {len(matches) - 1} other retrieved "
            f"chunk(s) ({', '.join(other_docs)}) — attributed to the highest-ranked match."
        )
    verdict_output.grounding_note = " ".join(note_parts)

    # Confidence auto-downgrade rule applies regardless of match tier —
    # a noise-tolerant match is still a real, grounded quote.
    if verdict_output.confidence < CONFIDENCE_DOWNGRADE_THRESHOLD and \
            verdict_output.verdict in (Verdict.COMPLIANT, Verdict.NON_COMPLIANT):
        verdict_output.grounding_note += (
            f" Confidence {verdict_output.confidence:.2f} is below the "
            f"{CONFIDENCE_DOWNGRADE_THRESHOLD} auto-downgrade threshold — deferred to "
            f"Requires Legal Review despite a correctly grounded quote."
        )
        verdict_output.verdict = Verdict.REQUIRES_LEGAL_REVIEW

    return verdict_output
