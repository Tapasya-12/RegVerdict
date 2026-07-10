"""
Builds an in-memory BM25 index from whatever's already in Qdrant.

Why rebuild BM25 from Qdrant rather than re-running the ingestion pipeline:
BM25 needs the full corpus in memory as tokenized documents (it's not an
ANN index you can incrementally query like dense vectors), but Qdrant is
already the single source of truth for chunk text + metadata after Phase 1.
Scrolling it once at startup keeps BM25 and dense search consistent by
construction — there's only one place chunk text lives.
"""

import re
from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Simple, fast tokenizer. Regulatory text has exact defined terms
    (e.g. 'NBFC-MFI') that a lemmatizing/stemming tokenizer could distort,
    so this deliberately stays dumb: lowercase + alphanumeric split."""
    return _TOKEN_RE.findall(text.lower())


def scroll_all_points(client, collection_name: str, batch_size: int = 256) -> list[dict]:
    """Pulls every point's id + payload out of a Qdrant collection.
    Fine for a few thousand clauses; if the corpus grows past ~50k chunks,
    this should move to a paginated/streaming BM25 build instead."""
    all_points = []
    next_offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(points)
        if next_offset is None:
            break

    return all_points


def build_bm25_corpus(client, collection_name: str) -> dict:
    """
    Returns:
        {
            "bm25": BM25Okapi instance,
            "point_ids": [id, ...],       # same order as tokenized_corpus
            "payloads": [payload, ...],   # same order, includes chunk text + metadata
        }
    """
    points = scroll_all_points(client, collection_name)
    if not points:
        raise ValueError(
            f"Collection '{collection_name}' is empty — run ingestion/embed_and_load.py first."
        )

    point_ids = []
    payloads = []
    tokenized_corpus = []

    for point in points:
        text = point.payload.get("text", "")
        if not text:
            continue  # skip any malformed/empty chunk rather than let it silently zero-weight everything
        point_ids.append(point.id)
        payloads.append(point.payload)
        tokenized_corpus.append(tokenize(text))

    bm25 = BM25Okapi(tokenized_corpus)
    return {"bm25": bm25, "point_ids": point_ids, "payloads": payloads}
