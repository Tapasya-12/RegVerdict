"""
Clause Graph backend — extracts cross-references between clauses WITHIN a
single document, powering the force-directed graph UI.

Design choice worth explaining: rather than guessing a citation regex per
document's numbering style (which we already know varies wildly — plain
integers, dotted multi-level, "Article N", lettered suffixes — a new
surprise every time we've added a document), this anchors against the
DOCUMENT'S OWN ALREADY-KNOWN clause_numbers. A reference only counts if
the number after a reference keyword ("Article", "Section", "paragraph",
etc.) matches a clause_number that actually exists in this document. This
sidesteps the whole "what format does this PDF use" problem and, just as
importantly, avoids false positives — a stray number near the word
"paragraph" that doesn't correspond to a real clause is ignored rather
than treated as a broken/dangling reference.

Deliberately intra-document only for now: cross-document reference
resolution (e.g. one RBI circular citing another by name) is a much
harder, riskier problem and out of scope here.
"""

import re
from collections import defaultdict

REFERENCE_KEYWORD_RE = re.compile(
    r"\b(?:Article|Section|Sec\.|Clause|Para\.?|paragraph|Chapter|§)\s+"
    r"(\d+[A-Za-z]?(?:\.\d+)*)",
    re.IGNORECASE,
)


def extract_references(chunk_text: str, own_clause_number: str,
                        known_clause_numbers: set) -> set:
    """
    Returns the set of clause_numbers this chunk's text references, from
    among known_clause_numbers, excluding a self-reference to its own
    clause_number.
    """
    found = set()
    for match in REFERENCE_KEYWORD_RE.finditer(chunk_text):
        candidate = match.group(1)
        if candidate == own_clause_number:
            continue  # self-reference (e.g. "paragraph 3 of this Article") — not a graph edge
        if candidate in known_clause_numbers:
            found.add(candidate)
    return found


def build_clause_graph(chunks: list[dict]) -> dict:
    """
    chunks: list of {clause_number, text, parent_section, document_name, ...}
    — all chunks belonging to ONE document.

    Returns {nodes: [{id, clause_number, parent_section}], edges: [{source, target}]}
    Edges are deduplicated; no self-loops.
    """
    known_clause_numbers = {c["clause_number"] for c in chunks}

    nodes = [
        {"id": c["clause_number"], "clause_number": c["clause_number"],
         "parent_section": c.get("parent_section", "")}
        for c in chunks
    ]

    edge_set = set()  # (source, target) tuples, for dedup
    for chunk in chunks:
        refs = extract_references(
            chunk.get("text", ""), chunk["clause_number"], known_clause_numbers
        )
        for ref in refs:
            edge_set.add((chunk["clause_number"], ref))

    edges = [{"source": s, "target": t} for s, t in sorted(edge_set)]

    return {"nodes": nodes, "edges": edges}
