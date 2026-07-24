"""
Phase 2 core: hybrid dense + BM25 retrieval, fused via Reciprocal Rank
Fusion (RRF), per design doc 2.3.

Why RRF specifically (not just averaging normalized scores): dense
similarity scores and BM25 scores live on completely different, non-
comparable scales. RRF sidesteps that by fusing on RANK POSITION instead
of raw score — a chunk ranked #1 by BM25 and #3 by dense search gets
credit for both, without needing to reconcile a cosine-similarity float
against a BM25 float.
"""

import sys
import threading
from pathlib import Path

# Make ingestion/ importable without requiring the caller to fiddle with PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))

from sentence_transformers import SentenceTransformer

from config import COLLECTION_NAME, EMBED_MODEL_NAME, get_qdrant_client  # noqa: E402
from retrieval_config import (  # noqa: E402
    DENSE_CANDIDATES_K, BM25_CANDIDATES_K, RRF_K, RERANK_CANDIDATE_POOL,
)
from bm25_index import build_bm25_corpus, tokenize  # noqa: E402
from reranker import CrossEncoderReranker  # noqa: E402


class HybridRetriever:
    def __init__(self):
        self.client = get_qdrant_client()
        self.embed_model = SentenceTransformer(EMBED_MODEL_NAME)

        print("[INFO] Building BM25 index from Qdrant collection ...")
        bm25_data = build_bm25_corpus(self.client, COLLECTION_NAME)
        self.bm25 = bm25_data["bm25"]
        self.bm25_point_ids = bm25_data["point_ids"]  # ordered, parallel to bm25 corpus
        # quick lookup: point_id -> payload, used to resolve both search paths to the same shape
        self.payload_by_id = {
            pid: payload for pid, payload in zip(bm25_data["point_ids"], bm25_data["payloads"])
        }
        print(f"[INFO] Ready — {len(self.bm25_point_ids)} chunks indexed for BM25 + dense search.")

        # Loaded on first use, not here — the cross-encoder is a separate
        # model download/load, and plenty of callers (e.g. the retrieve()
        # REPL below) never need it.
        self._reranker = None
        # FastAPI runs sync endpoints in a thread pool, and this retriever
        # is a shared singleton (tools.get_retriever()) — an unguarded
        # "if None: construct" here is a real race: concurrent first-use
        # requests can each see None and construct their own CrossEncoder
        # simultaneously, which crashes with a PyTorch meta-tensor error
        # (caught via a 25-concurrent-request rate-limit test). The lock
        # only guards construction, not every rerank() call — once built,
        # concurrent inference on the same model is fine.
        self._reranker_lock = threading.Lock()

    def dense_search(self, query: str, k: int = DENSE_CANDIDATES_K) -> list[tuple[str, int]]:
        """Returns [(point_id, rank), ...] ordered best-first, rank is 1-indexed."""
        query_vector = self.embed_model.encode(query, normalize_embeddings=True).tolist()
        # qdrant-client's embedded/local-path mode (config.QDRANT_URL unset —
        # the only mode available without Docker) is NOT safe for true
        # concurrent access, even from threads of the same process: a
        # 25-concurrent-request burst raised "Storage folder ... is already
        # accessed by another instance of Qdrant client". A Python-level
        # lock here was tried and reverted — it turned a clean, catchable
        # RuntimeError into requests hanging indefinitely instead (the lock
        # can only serialize the Python call, not whatever the underlying
        # Rust engine is actually blocked on), which is a worse failure
        # mode. This is exactly the limitation docker-compose.yml's qdrant
        # service comment already documents — real concurrent access needs
        # the real Qdrant server (QDRANT_URL), not a workaround here.
        hits = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=k,
        )
        return [(hit.id, rank) for rank, hit in enumerate(hits, start=1)]

    def bm25_search(self, query: str, k: int = BM25_CANDIDATES_K) -> list[tuple[str, int]]:
        """Returns [(point_id, rank), ...] ordered best-first, rank is 1-indexed."""
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # pair each score with its point_id, sort desc, take top-k
        scored = list(zip(self.bm25_point_ids, scores))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        top_k = scored[:k]

        return [(point_id, rank) for rank, (point_id, _score) in enumerate(top_k, start=1)]

    @staticmethod
    def reciprocal_rank_fusion(
        *ranked_lists: list[tuple[str, int]], rrf_k: int = RRF_K
    ) -> list[tuple[str, float]]:
        """
        Standard RRF: score(doc) = sum over lists of 1 / (rrf_k + rank).
        A doc that appears in only one list still scores, just lower than
        one that shows up near the top of both — which is exactly the
        "regulatory text has exact terms dense search under-weights"
        problem the design doc calls out: BM25 can rescue a doc dense
        search buried, and vice versa.
        """
        fused_scores: dict[str, float] = {}
        for ranked_list in ranked_lists:
            for point_id, rank in ranked_list:
                fused_scores.setdefault(point_id, 0.0)
                fused_scores[point_id] += 1.0 / (rrf_k + rank)

        return sorted(fused_scores.items(), key=lambda pair: pair[1], reverse=True)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Full hybrid retrieval for one query. Returns top_k chunks as
        payload dicts (each has clause_number, document_name, text, etc.),
        with fused_rrf_score attached for debugging/eval.
        """
        dense_results = self.dense_search(query)
        bm25_results = self.bm25_search(query)
        fused = self.reciprocal_rank_fusion(dense_results, bm25_results)

        results = []
        for point_id, score in fused[:top_k]:
            payload = dict(self.payload_by_id.get(point_id, {}))
            payload["_point_id"] = point_id
            payload["_fused_rrf_score"] = score
            results.append(payload)
        return results

    def retrieve_with_rerank(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Full hybrid retrieval + cross-encoder re-ranking for one query.
        Fetches RERANK_CANDIDATE_POOL fused candidates via retrieve(), then
        re-ranks them down to top_k with a cross-encoder that scores
        (query, candidate) jointly — see reranker.py for why that catches
        cases RRF's rank-fusion alone misses (e.g. same-topic chunks from
        the wrong document that both retrievers score highly on their own).
        """
        if self._reranker is None:
            with self._reranker_lock:
                if self._reranker is None:  # re-check: another thread may have built it while we waited
                    self._reranker = CrossEncoderReranker()
        candidates = self.retrieve(query, top_k=RERANK_CANDIDATE_POOL)
        return self._reranker.rerank(query, candidates, top_k=top_k)


if __name__ == "__main__":
    retriever = HybridRetriever()
    while True:
        query = input("\nQuery (empty to quit): ").strip()
        if not query:
            break
        for i, chunk in enumerate(retriever.retrieve(query, top_k=5), start=1):
            print(f"\n[{i}] score={chunk['_fused_rrf_score']:.4f} "
                  f"doc={chunk.get('document_name')} clause={chunk.get('clause_number')}")
            print(f"    {chunk.get('text', '')[:200]}...")
