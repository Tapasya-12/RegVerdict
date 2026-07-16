"""
Phase 1 - Step 2: raw page text -> clause-bounded chunks.

Strategy (per design doc 2.2 and roadmap Phase 1):
- Detect numbered clause headers (e.g. "5.2.1") via regex on line starts.
- Everything between one header and the next belongs to that clause.
- Carry the nearest preceding ALL-CAPS or Title-Case short line as
  `parent_section` (chapter/section title) so retrieval doesn't lose
  surrounding context when a chunk is returned in isolation.
- effective_date/regulator/document_name are filled in per-document by
  the caller (embed_and_load.py), since those come from filenames/config,
  not from clause text itself.
"""

import re
from config import CLAUSE_HEADER_REGEX, ARTICLE_HEADER_REGEX, TRAILING_CHROME_MARKERS

DECIMAL_HEADER_RE = re.compile(CLAUSE_HEADER_REGEX)
ARTICLE_HEADER_RE = re.compile(ARTICLE_HEADER_REGEX)


def _strip_trailing_chrome(text: str) -> str:
    """Cuts off site nav/footer boilerplate that gets glued onto whichever
    chunk happens to be last on a page, since nothing follows it to act as
    a clause boundary. See TRAILING_CHROME_MARKERS in config.py."""
    cut_at = min(
        (idx for marker in TRAILING_CHROME_MARKERS if (idx := text.find(marker)) != -1),
        default=-1,
    )
    return text[:cut_at].rstrip() if cut_at != -1 else text

# Heuristic for a "section title" line: short, no trailing period, mostly
# capitalized words, not itself a clause header.
def _looks_like_section_title(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80:
        return False
    if DECIMAL_HEADER_RE.match(line) or ARTICLE_HEADER_RE.match(line):
        return False
    words = line.split()
    if not words:
        return False
    cap_ratio = sum(1 for w in words if w[:1].isupper()) / len(words)
    return cap_ratio > 0.6


# How much more indented than the shallowest header a line may be and still
# count as a header. Nested sub-list items (e.g. a "1./2." list inside a
# definition's explanatory text) reuse the same "N. " numbering format as
# true top-level clauses but sit further right on the page — this tolerance
# is intentionally tight so those get treated as body text instead of new
# clause boundaries. Requires parse_pdf.py's layout=True extraction, which
# preserves each line's horizontal position as leading whitespace.
HEADER_INDENT_TOLERANCE = 2


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def chunk_pages_by_clause(pages: list[dict]) -> list[dict]:
    """
    Input: [{page_number, text}, ...] from parse_pdf.py
    Output: [{clause_number, text, parent_section, source_page}, ...]
    """
    all_lines = [
        raw_line.rstrip()
        for page in pages
        for raw_line in page["text"].split("\n")
    ]

    # Per-document header-pattern selection: if this document contains real
    # "Article N" header lines, that's its SOLE header pattern (see
    # ARTICLE_HEADER_REGEX's docstring in config.py) — the decimal pattern
    # is not also checked, so internally-numbered paragraphs ("1.", "2.")
    # inside an Article become body text, not separate clause boundaries.
    # Otherwise, fall back to the decimal pattern every RBI document uses.
    uses_article_numbering = any(
        ARTICLE_HEADER_RE.match(line.lstrip(" ")) for line in all_lines
    )
    header_re = ARTICLE_HEADER_RE if uses_article_numbering else DECIMAL_HEADER_RE

    # Establish the indentation of true clause headers from this document's
    # own layout, rather than a hard-coded column, since it varies by PDF.
    header_indents = [
        _line_indent(line)
        for line in all_lines
        if header_re.match(line.lstrip(" "))
    ]
    min_header_indent = min(header_indents) if header_indents else 0
    max_header_indent = min_header_indent + HEADER_INDENT_TOLERANCE

    chunks = []
    current_clause_number = None
    current_text_lines = []
    current_source_page = None
    current_parent_section = ""       # most recent section title seen so far
    clause_parent_section = ""        # section title that was active when THIS clause started

    def flush():
        if current_clause_number is not None and current_text_lines:
            text = _strip_trailing_chrome(" ".join(l.strip() for l in current_text_lines if l.strip()))
            if text:
                chunks.append({
                    "clause_number": current_clause_number,
                    "text": text,
                    "parent_section": clause_parent_section,
                    "source_page": current_source_page,
                })

    for page in pages:
        for raw_line in page["text"].split("\n"):
            line = raw_line.rstrip()
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            header_match = header_re.match(stripped) if indent <= max_header_indent else None

            if header_match:
                flush()  # close out the previous clause using ITS parent section
                current_clause_number = (
                    header_match.group(1) if header_re is ARTICLE_HEADER_RE
                    else header_match.group(1) or header_match.group(2)
                )
                remainder = stripped[header_match.end():].strip()
                current_text_lines = [remainder] if remainder else []
                current_source_page = page["page_number"]
                # lock in whatever section title was active *before* this
                # clause started — a section header appearing later belongs
                # to the next clause, not this one
                clause_parent_section = current_parent_section
            elif _looks_like_section_title(line):
                current_parent_section = line.strip()
            else:
                if current_clause_number is not None:
                    current_text_lines.append(line)
                # else: preamble text before the first numbered clause —
                # intentionally dropped (title pages, tables of contents)

    flush()  # final clause on the last page
    return chunks


def clause_boundary_accuracy_report(chunks: list[dict]) -> None:
    """Quick sanity check to eyeball against the Phase 1 exit criteria:
    '>=95% of clauses correctly boundary-detected on a 20-document sample'.
    This just prints stats; actual accuracy needs manual spot-check against
    the source PDF per the roadmap."""
    empty_clauses = [c for c in chunks if len(c["text"]) < 10]
    print(f"Total clauses detected: {len(chunks)}")
    print(f"Suspiciously short/empty clauses: {len(empty_clauses)} "
          f"(spot-check these first — likely boundary-detection misses)")


if __name__ == "__main__":
    from parse_pdf import parse_all_pdfs

    all_pages = parse_all_pdfs()
    for doc_name, pages in all_pages.items():
        print(f"\n--- {doc_name} ---")
        chunks = chunk_pages_by_clause(pages)
        clause_boundary_accuracy_report(chunks)
        if chunks:
            print("Sample clause:", chunks[0])
