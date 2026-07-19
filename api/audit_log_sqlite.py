"""
Audit log, now backed by SQLite (data/regverdict.db, same database as auth.py's
users table) instead of the earlier JSONL file. This is what a real foreign key
to users.id actually buys you: an audit entry cannot exist without a genuine
user behind it, and "everything user X did" is a real indexed query instead of
a string match against a loose 'user' field.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "regverdict.db"
# Actual path resolved via auth.DB_PATH at call sites — this constant exists
# only so this file can be imported standalone for testing.


def append_log(db_path, user_id: int, tool: str, policy_text: str, verdict: str = None,
                confidence: float = None, document_name: str = None, clause_number: str = None,
                grounding_verified: bool = None, proposed_change: str = None,
                status_flipped: bool = None) -> dict:
    """
    user_id MUST correspond to a real row in users.id — the foreign key
    constraint (with PRAGMA foreign_keys = ON) will reject anything else,
    which is the actual point: no more anonymous or fabricated audit entries.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    timestamp = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        """INSERT INTO audit_log
           (user_id, tool, policy_text, proposed_change, verdict, confidence,
            document_name, clause_number, grounding_verified, status_flipped, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, tool, policy_text, proposed_change, verdict, confidence,
         document_name, clause_number,
         None if grounding_verified is None else int(grounding_verified),
         None if status_flipped is None else int(status_flipped),
         timestamp),
    )
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()

    return {"id": entry_id, "user_id": user_id, "tool": tool, "policy_text": policy_text,
            "verdict": verdict, "confidence": confidence, "document_name": document_name,
            "clause_number": clause_number, "timestamp": timestamp}


def read_log(db_path, verdict: str = None, start_date: str = None, end_date: str = None,
             search: str = None, username: str = None) -> list[dict]:
    """
    Joins users to attach the real username to every row — this is the query
    that was impossible to do reliably against a JSONL file. All filters
    optional and combine with AND. Newest first.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT audit_log.*, users.username
        FROM audit_log
        JOIN users ON audit_log.user_id = users.id
        WHERE 1=1
    """
    params = []

    if verdict:
        query += " AND audit_log.verdict = ?"
        params.append(verdict)
    if start_date:
        query += " AND substr(audit_log.timestamp, 1, 10) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND substr(audit_log.timestamp, 1, 10) <= ?"
        params.append(end_date)
    if search:
        query += " AND audit_log.policy_text LIKE ?"
        params.append(f"%{search}%")
    if username:
        query += " AND users.username = ?"
        params.append(username)

    query += " ORDER BY audit_log.timestamp DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
