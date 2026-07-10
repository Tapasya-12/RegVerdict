"""
Phase 2 retrieval-specific config. Kept SEPARATE from ingestion/config.py
on purpose — Claude Code has been editing that file directly against your
real data (composite chunk_id, TRAILING_CHROME_MARKERS, etc.), so bolting
new constants onto it here avoids a merge headache.

This file assumes ingestion/config.py still exports (unchanged names):
    QDRANT_LOCAL_PATH, COLLECTION_NAME, EMBED_MODEL_NAME, BASE_DIR
If Claude Code renamed any of those while fixing Phase 1, update the
import at the top of retriever.py to match — nothing else here depends
on ingestion internals.
"""

from pathlib import Path

# --- Hybrid retrieval ---
DENSE_CANDIDATES_K = 20     # top-K from dense search, pre-fusion
BM25_CANDIDATES_K = 20      # top-K from BM25 search, pre-fusion
RRF_K = 60                  # reciprocal rank fusion constant (standard default)
FINAL_TOP_K = 5             # how many chunks actually go to the verdict engine

# --- Re-ranking ---
RERANK_CANDIDATE_POOL = 20  # how many fused candidates the cross-encoder scores
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- Eval ---
EVAL_DIR = Path(__file__).resolve().parent.parent / "eval"
GOLD_SET_PATH = EVAL_DIR / "gold_set.csv"
