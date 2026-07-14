"""
Persistent audit log, per the roadmap's Phase 3 intent ("every tool call...
is logged to build the audit trail used later in the UI's History panel")
— never actually built until now. Deliberately simple: an append-only JSONL
file, not a database. Good enough for a single-user local demo; if this
project ever gets multi-user or needs concurrent-write safety, swap this
for SQLite — the read_log()/append_log() interface below wouldn't need to
change at the call sites, only the implementation.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "audit_log.jsonl"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_log(entry: dict) -> dict:
    """
    Appends one audit record. Adds id/timestamp automatically — callers
    only need to supply the meaningful fields (policy_text, verdict, etc).
    Returns the full record (including generated id/timestamp) in case the
    caller wants to echo it back immediately.
    """
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return record


def read_log(verdict: str | None = None, start_date: str | None = None,
             end_date: str | None = None, search: str | None = None) -> list[dict]:
    """
    Reads and filters the log. All filters are optional and combine with AND.
    - verdict: exact match against the 'verdict' field
    - start_date / end_date: ISO date strings (YYYY-MM-DD), inclusive
    - search: case-insensitive substring match against policy_text
    Returns newest-first (most useful default for an audit view).
    """
    if not LOG_PATH.exists():
        return []

    records = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip a corrupted line rather than crash the whole log

    if verdict:
        records = [r for r in records if r.get("verdict") == verdict]

    if start_date:
        records = [r for r in records if r.get("timestamp", "")[:10] >= start_date]

    if end_date:
        records = [r for r in records if r.get("timestamp", "")[:10] <= end_date]

    if search:
        search_lower = search.lower()
        records = [r for r in records if search_lower in r.get("policy_text", "").lower()]

    records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return records
