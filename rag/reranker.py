"""
Phase 2 - re-ranking step, per design doc 2.3:
"a cross-encoder re-ranks the top ~20 hybrid candidates down to the 3-5
returned to the verdict engine, improving precision on ambiguous queries."

Why a separate re-ranking stage instead of just trusting RRF's top-5:
RRF fuses two retrievers that each score query vs. document independently
(bi-encoder style) — neither ever actually reads the query and the
candidate together. A cross-encoder scores (query, candidate) jointly,
which is slower (can't be pre-computed/indexed) but meaningfully more
accurate at the final small-N stage where that cost is affordable.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentence_transformers import CrossEncoder
from retrieval_config import RERANKER_MODEL_NAME, RERANK_CANDIDATE_POOL


class CrossEncoderReranker:
    def __init__(self, model_name: str = RERANKER_MODEL_NAME):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """
        candidates: list of payload dicts (must each have a 'text' field),
        typically the RRF_K-fused output from HybridRetriever before
        truncating to top_k — pass in ~20, not already-truncated top-5,
        or this step can't add anything the fusion step didn't already do.
        """
        if not candidates:
            return []

        pool = candidates[:RERANK_CANDIDATE_POOL]
        pairs = [[query, c.get("text", "")] for c in pool]
        scores = self.model.predict(pairs)

        for candidate, score in zip(pool, scores):
            candidate["_rerank_score"] = float(score)

        pool.sort(key=lambda c: c["_rerank_score"], reverse=True)
        return pool[:top_k]


if __name__ == "__main__":
    # Quick manual check against whatever the hybrid retriever returns.
    from retriever import HybridRetriever

    retriever = HybridRetriever()
    reranker = CrossEncoderReranker()

    query = input("Query: ").strip()
    fused_candidates = retriever.retrieve(query, top_k=RERANK_CANDIDATE_POOL)
    reranked = reranker.rerank(query, fused_candidates, top_k=5)

    for i, chunk in enumerate(reranked, start=1):
        print(f"\n[{i}] rerank_score={chunk['_rerank_score']:.4f} "
              f"(rrf_score={chunk['_fused_rrf_score']:.4f}) "
              f"doc={chunk.get('document_name')} clause={chunk.get('clause_number')}")
        print(f"    {chunk.get('text', '')[:200]}...")
