# RegVerdict — Build Guide (Phase 0 + Phase 1)

This covers **Phase 0 (Foundations)** and **Phase 1 (Data Layer)** from the roadmap,
fully working end to end. Later phases (Retrieval Core, MCP Server, Verdict Engine,
UI) will build on this — ask for the next phase once this is running.

## Phase 0 — Environment Setup

Run these in order, from wherever you want the project to live.

```bash
# 1. Create and enter the project (already scaffolded for you below)
cd RegVerdict

# 2. Create an isolated Python environment (use 3.10 or 3.11)
python3 -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Confirm the environment is reproducible
python -c "import pdfplumber, fitz, sentence_transformers, qdrant_client; print('OK')"
```

If step 4 prints `OK`, your dev environment is reproducible via one command —
that's the Phase 0 exit criterion satisfied.

### Regulatory scope (Phase 0 decision, per design doc)
v1 corpus = **RBI Master Directions** (KYC, fair lending practices, data
localisation). Download the PDFs yourself from the official RBI site
(rbi.org.in → Notifications → Master Directions) and drop them into:

```
data/raw_pdfs/
```

SEBI circulars and GDPR Articles are deferred to Phase 6 / the Jurisdiction
Comparator — don't add them yet.

## Phase 1 — Data Layer

### Step 1: Register each PDF in the manifest

Open `data/document_manifest.json` and add one entry per PDF filename
(without `.pdf`), e.g.:

```json
{
  "rbi_master_direction_kyc_2024": {
    "regulator": "RBI",
    "effective_date": "2024-01-01",
    "topic_tags": ["KYC", "data retention"],
    "supersedes_clause_id": ""
  }
}
```

This exists because clause text alone doesn't reliably state which
regulator issued it or its effective date — that has to come from you,
once, per document.

### Step 2: Run the pipeline

```bash
cd ingestion

# 2a. Sanity-check PDF text extraction alone
python parse_pdf.py

# 2b. Sanity-check clause boundary detection alone
python clause_chunker.py

# 2c. Full pipeline: parse -> chunk -> embed -> store in Qdrant (local, embedded — no server needed)
python embed_and_load.py
```

`embed_and_load.py` downloads the `BAAI/bge-small-en-v1.5` embedding model
the first time it runs (~130MB) and stores vectors in
`data/qdrant_store/` — a local, file-based Qdrant instance. Nothing needs
to be started separately.

### Step 3: Spot-check boundary detection

`clause_chunker.py`'s `clause_boundary_accuracy_report()` prints how many
detected clauses look suspiciously short/empty — manually check those
against the source PDF first. Roadmap's Phase 1 exit criterion is **≥95%
correct boundary detection on a 20-document sample**; this script gets you
most of the way, but the regex (`CLAUSE_HEADER_REGEX` in `config.py`) may
need tuning per document format (some RBI PDFs use "5.2.1", others "Para 5.2.1").

## What's next

Phase 2 (Retrieval Core: hybrid dense + BM25 search, re-ranking, the 50-question
gold set and Recall@5 eval) builds directly on the Qdrant collection created here.
Say "continue to Phase 2" and I'll build that next, same way — real code, not
just a description.
