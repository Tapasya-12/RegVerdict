"""
Thin HTTP wrapper around mcp_server/tools.check_compliance, for the React
frontend (frontend/) to call directly over fetch() — the MCP server itself speaks stdio/MCP
protocol, not plain HTTP, so this is a separate small FastAPI process rather
than a change to mcp_server/server.py.

Run with: uvicorn server:app --reload --port 8000 (from this directory).
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# auth.py reads JWT_SECRET_KEY from the environment at import time, so the
# .env it lives in (mcp_server/.env — reused here rather than adding a
# second env file, since llm_client.py already loads it the same way) must
# be loaded before `import auth` runs, not left to depend on import order.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / "mcp_server" / ".env")

import jwt  # noqa: E402
from fastapi import Depends, FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import audit_log_sqlite  # noqa: E402
import auth  # noqa: E402
import recent_queries  # noqa: E402
import tools  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    auth.init_db()
    yield


app = FastAPI(title="RegVerdict API", lifespan=lifespan)

# Vite picks whichever port is free (5173, 5174, ...) — match any localhost
# port instead of hardcoding one, since the frontend is a separate dev process.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        return auth.decode_access_token(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def get_current_user_id(username: str = Depends(get_current_user)) -> int:
    # audit_log_sqlite/recent_queries key everything off the real integer
    # user_id (foreign key to users.id), never the username string — this
    # is the one place that resolves the validated token back to that id.
    user = auth.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user["id"]


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class RecentQueryCreate(BaseModel):
    full_query: str
    display_title: str | None = None


class RecentQueryRename(BaseModel):
    display_title: str


class CheckComplianceRequest(BaseModel):
    policy_text: str


class SimulatePolicyChangeRequest(BaseModel):
    original_policy: str
    proposed_change: str


class CompareJurisdictionsRequest(BaseModel):
    policy_text: str
    regulators: list[str]


@app.get("/api/health")
def health() -> dict:
    # Also pre-warms tools.get_retriever()'s singleton (embedding model +
    # BM25 index build) so the first real check_compliance call isn't the
    # one paying that cold-start cost. Deliberately unprotected — useful for
    # infra checks that shouldn't need a session.
    retriever = tools.get_retriever()
    return {"status": "ok", "indexed_chunks": len(retriever.payload_by_id)}


@app.post("/api/auth/signup")
def signup(req: SignupRequest) -> dict:
    try:
        return auth.create_user(req.username, req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    user = auth.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": auth.create_access_token(user["username"]), "token_type": "bearer"}


def _verdict_str(v):
    # verdict_output.model_dump() (mode="python", the default) leaves
    # "verdict" as a raw Verdict enum member — fine for FastAPI's own JSON
    # response encoding, but str(Verdict.NON_COMPLIANT) would render as
    # "Verdict.NON_COMPLIANT" instead of "Non-Compliant" anywhere else
    # (audit log rows, summary strings), so callers normalize through here.
    return v.value if hasattr(v, "value") else v


@app.post("/api/check_compliance")
def check_compliance(req: CheckComplianceRequest, user_id: int = Depends(get_current_user_id)) -> dict:
    if not req.policy_text or not req.policy_text.strip():
        raise HTTPException(status_code=400, detail="policy_text must be a non-empty string")

    result = tools.check_compliance(req.policy_text)

    source_clause = result.get("source_clause") or {}
    audit_log_sqlite.append_log(
        auth.DB_PATH,
        user_id,
        tool="check_compliance",
        policy_text=req.policy_text,
        verdict=_verdict_str(result.get("verdict")),
        confidence=result.get("confidence"),
        document_name=source_clause.get("document") if source_clause else None,
        clause_number=source_clause.get("clause_number") if source_clause else None,
        grounding_verified=result.get("grounding_verified"),
    )

    # This endpoint is only ever called from the Workspace tool (Policy Diff
    # and Compare Jurisdictions call tools.check_compliance() directly as a
    # Python function via their own endpoints, not this route) — so every
    # hit here is a real Workspace submission that belongs in the sidebar.
    recent_queries.create_recent_query(auth.DB_PATH, user_id, req.policy_text)

    return result


@app.post("/api/simulate_policy_change")
def simulate_policy_change(
    req: SimulatePolicyChangeRequest, user_id: int = Depends(get_current_user_id)
) -> dict:
    if not req.original_policy or not req.original_policy.strip():
        raise HTTPException(status_code=400, detail="original_policy must be a non-empty string")
    if not req.proposed_change or not req.proposed_change.strip():
        raise HTTPException(status_code=400, detail="proposed_change must be a non-empty string")

    result = tools.simulate_policy_change(req.original_policy, req.proposed_change)

    original_verdict = _verdict_str(result.get("original_verdict", {}).get("verdict"))
    proposed_verdict = _verdict_str(result.get("proposed_verdict", {}).get("verdict"))
    audit_log_sqlite.append_log(
        auth.DB_PATH,
        user_id,
        tool="simulate_policy_change",
        policy_text=req.original_policy,
        proposed_change=req.proposed_change,
        verdict=f"{original_verdict} → {proposed_verdict}",
        status_flipped=result.get("status_flipped"),
    )

    return result


@app.post("/api/compare_jurisdictions")
def compare_jurisdictions(
    req: CompareJurisdictionsRequest, user_id: int = Depends(get_current_user_id)
) -> dict:
    if not req.policy_text or not req.policy_text.strip():
        raise HTTPException(status_code=400, detail="policy_text must be a non-empty string")
    if not req.regulators:
        raise HTTPException(status_code=400, detail="regulators must be a non-empty list")

    result = tools.compare_jurisdictions(req.policy_text, req.regulators)

    # No single clause/confidence to log here — each regulator in the
    # comparison has its own, so the audit entry carries a per-regulator
    # verdict summary instead (mirrors simulate_policy_change's
    # "before → after" summary string for the same reason).
    results_by_regulator = result.get("results_by_regulator", {})
    verdict_summary = " · ".join(
        f"{regulator}: {_verdict_str(r.get('verdict'))}"
        for regulator, r in results_by_regulator.items()
    )
    audit_log_sqlite.append_log(
        auth.DB_PATH,
        user_id,
        tool="compare_jurisdictions",
        policy_text=req.policy_text,
        verdict=verdict_summary,
    )

    return result


@app.get("/api/documents")
def documents(current_user: str = Depends(get_current_user)) -> list[str]:
    retriever = tools.get_retriever()
    return sorted({
        p.get("document_name") for p in retriever.payload_by_id.values()
        if p.get("document_name")
    })


@app.get("/api/clause_graph/{document_name}")
def clause_graph(document_name: str, current_user: str = Depends(get_current_user)) -> dict:
    # Read-only structural query, not a compliance verdict — no audit_log entry.
    result = tools.get_clause_graph(document_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# fetch_regulation / generate_compliance_report / detect_regulatory_conflicts /
# get_regulation_history: these 4 MCP tools (mcp_server/tools.py) were only
# ever wired into the MCP protocol server (mcp_server/server.py) for stdio
# MCP clients — checked git history, they were never exposed here for the
# React frontend, so there's nothing to "restore" so much as add for the
# first time. None of the 5 built frontend tools call these yet, so — like
# clause_graph/documents above — no audit_log entry or recent_queries side
# effect; they're plain protected reads, same pattern as the rest of this
# file's read-only endpoints.
# ---------------------------------------------------------------------------

@app.get("/api/fetch_regulation")
def fetch_regulation(topic: str, top_k: int = 5, current_user: str = Depends(get_current_user)) -> dict:
    if not topic or not topic.strip():
        raise HTTPException(status_code=400, detail="topic must be a non-empty string")
    return tools.fetch_regulation(topic, top_k)


@app.post("/api/generate_compliance_report")
def generate_compliance_report(
    req: CheckComplianceRequest, current_user: str = Depends(get_current_user)
) -> dict:
    if not req.policy_text or not req.policy_text.strip():
        raise HTTPException(status_code=400, detail="policy_text must be a non-empty string")
    return tools.generate_compliance_report(req.policy_text)


@app.post("/api/detect_regulatory_conflicts")
def detect_regulatory_conflicts(
    req: CheckComplianceRequest, current_user: str = Depends(get_current_user)
) -> dict:
    if not req.policy_text or not req.policy_text.strip():
        raise HTTPException(status_code=400, detail="policy_text must be a non-empty string")
    return tools.detect_regulatory_conflicts(req.policy_text)


@app.get("/api/regulation_history/{clause_id}")
def get_regulation_history(clause_id: str, current_user: str = Depends(get_current_user)) -> dict:
    return tools.get_regulation_history(clause_id)


@app.get("/api/audit_trail")
def audit_trail(
    verdict: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    current_user: str = Depends(get_current_user),
) -> list[dict]:
    # Deliberately not scoped to current_user — an audit trail's whole point
    # is visibility across the firm's compliance activity, not a private
    # history. (Contrast with recent_queries below, which is per-user by
    # design and enforces it at the storage layer, not just the query.)
    return audit_log_sqlite.read_log(
        auth.DB_PATH, verdict=verdict, start_date=start_date, end_date=end_date, search=search
    )


@app.post("/api/recent_queries")
def create_recent_query_endpoint(
    req: RecentQueryCreate, user_id: int = Depends(get_current_user_id)
) -> dict:
    return recent_queries.create_recent_query(auth.DB_PATH, user_id, req.full_query, req.display_title)


@app.get("/api/recent_queries")
def list_recent_queries_endpoint(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    return recent_queries.list_recent_queries(auth.DB_PATH, user_id)


@app.patch("/api/recent_queries/{query_id}/pin")
def pin_recent_query_endpoint(query_id: int, user_id: int = Depends(get_current_user_id)) -> dict:
    try:
        return recent_queries.toggle_pin(auth.DB_PATH, query_id, user_id)
    except ValueError as e:
        # Same message whether the id doesn't exist at all or belongs to
        # someone else — the caller shouldn't be able to tell those apart.
        raise HTTPException(status_code=404, detail=str(e))


@app.patch("/api/recent_queries/{query_id}")
def rename_recent_query_endpoint(
    query_id: int, req: RecentQueryRename, user_id: int = Depends(get_current_user_id)
) -> dict:
    try:
        return recent_queries.rename_query(auth.DB_PATH, query_id, user_id, req.display_title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/recent_queries/{query_id}")
def delete_recent_query_endpoint(query_id: int, user_id: int = Depends(get_current_user_id)) -> dict:
    deleted = recent_queries.delete_query(auth.DB_PATH, query_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Query not found or does not belong to this user.")
    return {"deleted": True}
