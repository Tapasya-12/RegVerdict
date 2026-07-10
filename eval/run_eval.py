"""
Phase 2 exit criterion: Recall@5 >= 0.85 on a 50-question gold set.

A query is scored as a "hit" if the expected_document (and expected_clause_number,
when filled in) appears anywhere in the top-5 retrieved chunks. Matching is
deliberately lenient on clause_number — leave it blank in gold_set.csv while
you're still building out the set, and the eval just checks the right
DOCUMENT was retrieved. Tighten to exact clause matching once the gold set
is stable, since document-level recall is a much weaker signal than
clause-level recall.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))

from retriever import HybridRetriever  # noqa: E402
from retrieval_config import GOLD_SET_PATH  # noqa: E402


def load_gold_set(path: Path = GOLD_SET_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Gold set at {path} is empty.")
    return rows


def is_hit(retrieved_chunks: list[dict], expected_document: str, expected_clause_number: str) -> bool:
    for chunk in retrieved_chunks:
        doc_match = chunk.get("document_name") == expected_document
        if not doc_match:
            continue
        if not expected_clause_number:  # document-level check only
            return True
        if chunk.get("clause_number") == expected_clause_number:
            return True
    return False


def run_eval(top_k: int = 5) -> None:
    gold_set = load_gold_set()
    retriever = HybridRetriever()

    hits = 0
    misses = []

    for row in gold_set:
        query = row["query"].strip()
        expected_doc = row["expected_document"].strip()
        expected_clause = row.get("expected_clause_number", "").strip()

        retrieved = retriever.retrieve_with_rerank(query, top_k=top_k)
        if is_hit(retrieved, expected_doc, expected_clause):
            hits += 1
        else:
            misses.append({
                "query": query,
                "expected_document": expected_doc,
                "expected_clause_number": expected_clause,
                "got_documents": [c.get("document_name") for c in retrieved],
            })

    total = len(gold_set)
    recall_at_k = hits / total if total else 0.0

    print(f"\n=== Recall@{top_k}: {recall_at_k:.3f} ({hits}/{total}) ===")
    print(f"Exit criterion (roadmap Phase 2): Recall@5 >= 0.85 — "
          f"{'PASS' if recall_at_k >= 0.85 else 'NOT YET'}")

    if misses:
        print(f"\n--- {len(misses)} misses (debug these first) ---")
        for m in misses:
            print(f"\nQuery: {m['query']}")
            print(f"  Expected: {m['expected_document']} / {m['expected_clause_number'] or '(any clause)'}")
            print(f"  Got docs: {m['got_documents']}")


if __name__ == "__main__":
    run_eval()
