"""
Phase 1 - Step 3: chunks -> embeddings -> Qdrant.

Uses Qdrant in embedded/local mode (QdrantClient(path=...)) so there is
NO separate server to run for local development. Swap to a hosted/Docker
Qdrant later (Phase 6 hardening) by changing QDRANT_LOCAL_PATH usage to
QdrantClient(url=...) — the rest of the code doesn't change.
"""

import json
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import (
    QDRANT_LOCAL_PATH, COLLECTION_NAME, EMBED_MODEL_NAME, EMBED_DIM, BASE_DIR,
    build_chunk_id,
)
from parse_pdf import parse_all_pdfs
from clause_chunker import chunk_pages_by_clause

MANIFEST_PATH = BASE_DIR / "data" / "document_manifest.json"


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    manifest.pop("_comment", None)
    manifest.pop("_example", None)
    return manifest


def get_client() -> QdrantClient:
    client = QdrantClient(path=QDRANT_LOCAL_PATH)
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
    return client


def build_chunk_records(manifest: dict) -> list[dict]:
    """Runs the full parse -> chunk pipeline and attaches per-document
    metadata from the manifest. Returns flat list of chunk dicts ready
    to embed."""
    all_pages = parse_all_pdfs()
    records = []
    seen_chunk_id_counts: dict[str, int] = {}

    for doc_name, pages in all_pages.items():
        if doc_name not in manifest:
            print(f"[WARN] '{doc_name}' has no entry in document_manifest.json — "
                  f"skipping. Add regulator/effective_date/topic_tags first.")
            continue

        doc_meta = manifest[doc_name]
        chunks = chunk_pages_by_clause(pages)

        for chunk in chunks:
            chunk_id = build_chunk_id(doc_name, chunk["parent_section"], chunk["clause_number"], chunk["source_page"])
            # Safety net: even (document, section, clause, page) can coincide
            # when a source document itself reuses a label twice on one page.
            # Suffix repeats with an occurrence count so chunk_id is always
            # unique, rather than silently overwriting one chunk's Qdrant
            # point with another's on upsert.
            seen_chunk_id_counts[chunk_id] = seen_chunk_id_counts.get(chunk_id, 0) + 1
            occurrence = seen_chunk_id_counts[chunk_id]
            if occurrence > 1:
                chunk_id = f"{chunk_id}::{occurrence}"

            records.append({
                "chunk_id": chunk_id,
                "document_name": doc_name,
                "regulator": doc_meta.get("regulator", ""),
                "clause_number": chunk["clause_number"],
                "effective_date": doc_meta.get("effective_date", ""),
                "topic_tags": doc_meta.get("topic_tags", []),
                "supersedes_clause_id": doc_meta.get("supersedes_clause_id", ""),
                "superseded_by_clause_id": "",  # filled in later once amendment is ingested
                "parent_section": chunk["parent_section"],
                "source_page": chunk["source_page"],
                "text": chunk["text"],
            })

    return records


def embed_and_upsert(records: list[dict], batch_size: int = 64) -> None:
    if not records:
        print("[INFO] No chunk records to embed. Check raw_pdfs/ and manifest.")
        return

    model = SentenceTransformer(EMBED_MODEL_NAME)
    client = get_client()

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        texts = [r["text"] for r in batch]
        vectors = model.encode(texts, normalize_embeddings=True).tolist()

        points = []
        for record, vector in zip(batch, vectors):
            payload = {k: v for k, v in record.items() if k != "text"}
            payload["text"] = record["text"]  # keep raw text for display/citation checks
            # Point id is derived from chunk_id (not random) so re-ingesting
            # the same document upserts in place instead of duplicating —
            # and so a chunk can be looked up by its composite id directly.
            points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, record["chunk_id"])),
                vector=vector,
                payload=payload,
            ))

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"[INFO] Upserted {len(points)} chunks ({i + len(points)}/{len(records)})")

    print(f"[DONE] {len(records)} clauses embedded and stored in '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    manifest = load_manifest()
    records = build_chunk_records(manifest)
    print(f"[INFO] {len(records)} clause chunks ready across {len(manifest)} manifested documents.")
    embed_and_upsert(records)
