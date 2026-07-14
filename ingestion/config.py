"""
Central config for the ingestion pipeline.
Keep every path / model name / schema definition here so nothing is
hard-coded twice across parse_pdf.py, clause_chunker.py, embed_and_load.py.
"""

import os
import re
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QDRANT_LOCAL_PATH = str(BASE_DIR / "data" / "qdrant_store")  # embedded, no server needed

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

# --- Embedding model ---
# Good general-purpose open model. Swap to a domain-tuned one later if
# Recall@5 on the gold set (Phase 2) comes in weak on regulatory jargon.
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384

# --- Qdrant collection ---
COLLECTION_NAME = "regverdict_clauses"

# --- Clause metadata schema (per design doc section 2.2) ---
# Every chunk stored in Qdrant carries this payload shape.
CHUNK_METADATA_FIELDS = [
    "chunk_id",          # composite, document-wide-unique — see build_chunk_id()
    "document_name",
    "regulator",        # e.g. "RBI", "SEBI", "GDPR"
    "clause_number",     # e.g. "5.2.1" — NOT unique on its own (preamble
                          # recitals and embedded annex Orders restart their
                          # own numbering), only unique combined with
                          # parent_section. Use chunk_id for lookups.
    "effective_date",    # ISO date string, "" if unknown
    "topic_tags",        # list[str]
    "supersedes_clause_id",
    "superseded_by_clause_id",
    "parent_section",    # chapter/section title for surrounding context
    "source_page",       # page number in the source PDF
]


# --- Known trailing site-chrome to strip ---
# Some source PDFs are browser "print to PDF" captures of the RBI website
# rather than a clean document export, so page nav/footer chrome (site map,
# social links, browser-support notice, etc.) sometimes gets glued onto the
# last real chunk on the page, since nothing follows it to act as a clause
# boundary. Anything from the first matching marker onward is stripped.
TRAILING_CHROME_MARKERS = ["Back to previous page"]


def build_chunk_id(document_name: str, parent_section: str, clause_number: str, source_page: int) -> str:
    """Composite identifier used wherever a chunk needs to be looked up or
    referenced. clause_number alone collides across a document's preamble
    and embedded annexes (each restarts its own numbering at 1). Even
    (parent_section, clause_number) can collide when two embedded annexes
    share identical boilerplate (e.g. an identical distribution-list
    section title) — source_page breaks that remaining tie since the two
    occurrences are never on the same page."""
    return f"{document_name}::{parent_section}::{clause_number}::{source_page}"

# --- Clause header detection regex ---
# Matches numbered clause headers like "5.2.1", "5.2", "12.", "33A.",
# "6A.1", "Para 5.2.1" at the start of a line. Two alternatives, in one
# alternation so both land in a predictable group pair (group 1 =
# multi-level, group 2 = single-level):
#   - multi-level: "5.2" / "5.2.1" / "6A.1" / "5.2.1." — trailing period
#     optional. The leading number may itself carry a letter suffix, since
#     some documents label a whole SECTION "6A" and then dot-number its own
#     sub-clauses "6A.1", "6A.2", ... directly off that (no space before
#     the dot, unlike the single-level letter-suffix case below).
#   - single-level: "12." / "33A." — trailing period REQUIRED, optional
#     trailing uppercase letter. RBI Master Directions commonly use one
#     continuously-numbered sequence of top-level paragraphs (e.g.
#     "1. Short Title...", "74. All the repealed circulars...") rather than
#     decimal "5.2.1"-style numbering, and later amendments often insert new
#     paragraphs as "33A."/"33B." between existing numbers instead of
#     renumbering everything below. The period is mandatory here so bare
#     numbers inside prose (e.g. "5 percent") don't get misread as headers.
# The two alternatives don't collide: multi-level requires a digit
# immediately after the dot ("6A.1"), single-level requires whitespace
# immediately after the dot ("33A. "), so a given line can only match one.
# Caller (clause_chunker.py) should read whichever of group(1)/group(2) matched,
# and should gate matches by indentation (see HEADER_INDENT_TOLERANCE there) —
# nested sub-list items inside clause bodies reuse this same "N. " format.
CLAUSE_HEADER_REGEX = r"^(?:Para\s+)?(?:(\d{1,3}[A-Z]?(?:\.\d{1,3}){1,3})\.?|(\d{1,3}[A-Z]?)\.)\s+"


# --- Near-empty "stub" chunk detection ---
# Some source documents (e.g. rbi_interest_rate_advances) include an
# appendix/bibliography listing every circular ever superseded, numbered in
# the SAME sequence as the real substantive clauses (clause numbers 1-61
# there mix real rules with circular-index entries). These stub chunks are
# just a circular reference + a date, with zero rule content, e.g.:
#   "DBOD.No.Dir.BC.141/13.07.01-94   07.12.1994 Interest Rates on Advances"
#   "Mail Box clarification          27.04.2012 Guidelines on Base Rate"
# Confirmed via Phase 4 investigation into a real retrieval miss (a query
# about the Base Rate returned one of these stubs instead of the actual
# substantive clause). Deliberately NOT a word-count filter — this corpus
# has genuine one-sentence rules as short as 7 words (e.g. "REs shall frame
# a Customer Acceptance Policy."), so length alone can't separate the two;
# only the citation/deletion-marker shape can.
CIRCULAR_STUB_REGEX = re.compile(
    r"^\s*(DBOD|DBR|IECD|Mail\s?Box|Letter to IBA)\b.*\d{2}[.:]\d{2}[.:]\d{2,4}",
    re.IGNORECASE,
)
DELETED_STUB_REGEX = re.compile(r"^\s*\d{0,4}\s*Deleted\.?\d*\s*$", re.IGNORECASE)


def is_stub_chunk(text: str) -> bool:
    """True for circular-citation bibliography entries or bare 'Deleted'
    placeholders — chunks with zero rule content that should never enter
    the corpus. Called at chunk-build time, before embedding."""
    stripped = text.strip()
    return bool(CIRCULAR_STUB_REGEX.match(stripped) or DELETED_STUB_REGEX.match(stripped))
