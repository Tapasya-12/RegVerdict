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

import tools  # noqa: E402

app = FastAPI(title="RegVerdict API")

# Vite dev server's default origin — the UI is a separate process on 5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class CheckComplianceRequest(BaseModel):
    policy_text: str


@app.post("/api/check_compliance")
def check_compliance(req: CheckComplianceRequest) -> dict:
    if not req.policy_text or not req.policy_text.strip():
        raise HTTPException(status_code=400, detail="policy_text must be a non-empty string")
    return tools.check_compliance(req.policy_text)
