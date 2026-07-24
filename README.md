# RegVerdict

An AI-powered regulatory compliance copilot. Describe a business policy in plain English, and RegVerdict tells you whether it complies with real regulations (currently RBI and GDPR) — citing the exact source clause, and verifying its own citation against the source text before showing you an answer.

## What it does

- **Compliance Workspace** — chat-style interface: describe a policy, get a grounded verdict (Compliant / Non-Compliant / Requires Legal Review / Conflicting Regulations) with the exact clause cited.
- **Policy Diff** — compare a current policy against a proposed change, see if the compliance verdict flips.
- **Compare Jurisdictions** — run the same policy against multiple regulators (RBI, GDPR) side by side.
- **Audit Trail** — full history of every check run, filterable by verdict/date/user, exportable as CSV.
- **Clause Graph** — visualizes how regulatory clauses cross-reference each other within a document.
- **Word export** — download any compliance verdict as a formatted `.docx` report.

## Why it's trustworthy, not just plausible

Every verdict's cited quote is programmatically checked against the actual source clause text before it's ever shown. If the citation can't be verified, the system downgrades to "Requires Legal Review" rather than displaying a confident answer it can't back up. Confidence below 90% triggers the same downgrade, regardless of grounding.

## Architecture

```
frontend/          React + Vite — the UI
api/                FastAPI — HTTP layer, auth, rate limiting
mcp_server/         MCP tools (7 core tools) + Groq-based verdict engine
rag/                Hybrid retrieval: dense embeddings + BM25 + cross-encoder reranking
ingestion/          PDF → clause-chunked → embedded pipeline
eval/               Retrieval and verdict-accuracy regression tests
data/               Qdrant vector store (or Docker volume) + SQLite (users, audit log, documents, recent queries)
```

**Data flow**: PDF regulatory documents → clause-boundary chunking → embedding → Qdrant (hybrid dense+BM25 search) → retrieved clauses + policy text → Groq LLM → structured verdict → grounding check against source text → shown to user.

## Running it

### Option A — Docker (recommended)

```bash
docker compose --env-file .env.docker up --build
```

First time only, populate the vector store:
```bash
docker compose run --rm -e QDRANT_URL=http://qdrant:6333 backend python ingestion/embed_and_load.py
```

App runs at `http://localhost:5173`, API at `http://localhost:8000`.

### Option B — Local (no Docker)

```bash
# Backend
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
uvicorn api.server:app --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Requires a `.env` file (see `.env.example`) with `GROQ_API_KEY` and `JWT_SECRET_KEY`.

## Corpus

Currently indexed: RBI Master Directions (KYC, Interest Rate on Advances, Microfinance Fair Practices) and GDPR (Regulation 2016/679) — ~360 clauses total. Add a new document by placing the PDF in `data/raw_pdfs/`, registering it in `data/document_manifest.json`, and running `ingestion/embed_and_load.py`.

## Known limitations

- Regulation Timeline (amendment history over time) is not yet populated — requires ingesting multiple historical versions of a document, which hasn't been done.
- Two RBI clauses have minor extraction artifacts from PDF parsing (documented in `eval/` test notes) that occasionally cause a correct citation to fail strict verbatim matching; the grounding check's noise-tolerant fallback catches most of these.
- Password reset is not yet implemented — signup/login only.

## Testing

```bash
python eval/run_eval.py           # retrieval Recall@5 (currently ~0.925)
python eval/run_regression.py     # verdict accuracy + grounding safety (currently 85% accuracy, 0 dangerous ungrounded verdicts)
```