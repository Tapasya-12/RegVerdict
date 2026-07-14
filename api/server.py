"""
Thin HTTP wrapper around mcp_server/tools.check_compliance, for the React
frontend (frontend/) to call directly over fetch() — the MCP server itself speaks stdio/MCP
protocol, not plain HTTP, so this is a separate small FastAPI process rather
than a change to mcp_server/server.py.

Run with: uvicorn server:app --reload --port 8000 (from this directory).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import audit_log  # noqa: E402
import tools  # noqa: E402

app = FastAPI(title="RegVerdict API")

# Vite dev server's default origin — the frontend is a separate process on 5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class CheckComplianceRequest(BaseModel):
    policy_text: str


@app.get("/api/health")
def health() -> dict:
    # Also pre-warms tools.get_retriever()'s singleton (embedding model +
    # BM25 index build) so the first real check_compliance call isn't the
    # one paying that cold-start cost.
    retriever = tools.get_retriever()
    return {"status": "ok", "indexed_chunks": len(retriever.payload_by_id)}


@app.post("/api/check_compliance")
def check_compliance(req: CheckComplianceRequest) -> dict:
    if not req.policy_text or not req.policy_text.strip():
        raise HTTPException(status_code=400, detail="policy_text must be a non-empty string")

    result = tools.check_compliance(req.policy_text)

    source_clause = result.get("source_clause") or {}
    audit_log.append_log({
        "policy_text": req.policy_text,
        "verdict": result.get("verdict"),
        "confidence": result.get("confidence"),
        "document_name": source_clause.get("document") if source_clause else None,
        "clause_number": source_clause.get("clause_number") if source_clause else None,
        "grounding_verified": result.get("grounding_verified"),
    })

    return result


@app.get("/api/audit_trail")
def audit_trail(
    verdict: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
) -> list[dict]:
    return audit_log.read_log(verdict=verdict, start_date=start_date, end_date=end_date, search=search)
