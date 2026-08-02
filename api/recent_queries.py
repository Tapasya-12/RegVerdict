"""
Server-side storage for the sidebar's recent/pinned query list — replaces the
localStorage-only version. Tied to a real user_id via foreign key, so a
person's history follows them across devices/browsers instead of living only
in whichever browser they first used.
"""

import json
import sqlite3
from datetime import datetime, timezone


def create_session(db_path, user_id: int, user_text: str, assistant_result: dict, display_title: str = None) -> int:
    """Starts a new sidebar entry representing one conversation session,
    seeded with its first user/assistant turn. display_title is fixed here,
    from this FIRST query only — append_turn() below never touches it, so
    later turns in the same session don't rename it out from under the user."""
    if display_title is None:
        display_title = user_text[:60] + ("…" if len(user_text) > 60 else "")

    now = datetime.now(timezone.utc).isoformat()
    messages = [
        {"role": "user", "content": user_text, "timestamp": now},
        {"role": "assistant", "content": assistant_result, "timestamp": now},
    ]

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.execute(
        """INSERT INTO recent_queries (user_id, display_title, full_query, pinned, messages, created_at, updated_at)
           VALUES (?, ?, ?, 0, ?, ?, ?)""",
        (user_id, display_title, user_text, json.dumps(messages), now, now),
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def append_turn(db_path, session_id: int, user_id: int, user_text: str, assistant_result: dict) -> None:
    """Appends one user+assistant turn to an EXISTING session — never
    creates a new sidebar row, which is the whole point: every query
    submitted in the same ongoing conversation lands in the same entry.
    Raises ValueError if the session doesn't exist or belongs to someone
    else, same ownership guard as toggle_pin/rename_query/delete_query below."""
    conn = sqlite3.connect(db_path)
    existing = _get_owned_query(conn, session_id, user_id)
    if not existing:
        conn.close()
        raise ValueError("Session not found or does not belong to this user.")

    now = datetime.now(timezone.utc).isoformat()
    messages = json.loads(existing["messages"] or "[]")
    messages.append({"role": "user", "content": user_text, "timestamp": now})
    messages.append({"role": "assistant", "content": assistant_result, "timestamp": now})

    conn.execute(
        "UPDATE recent_queries SET messages = ?, updated_at = ? WHERE id = ?",
        (json.dumps(messages), now, session_id),
    )
    conn.commit()
    conn.close()


def create_recent_query(db_path, user_id: int, full_query: str, display_title: str = None) -> dict:
    """display_title defaults to a truncated version of full_query if not given."""
    if display_title is None:
        display_title = full_query[:60] + ("…" if len(full_query) > 60 else "")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """INSERT INTO recent_queries (user_id, display_title, full_query, pinned, created_at, updated_at)
           VALUES (?, ?, ?, 0, ?, ?)""",
        (user_id, display_title, full_query, now, now),
    )
    conn.commit()
    query_id = cursor.lastrowid
    conn.close()
    return {"id": query_id, "user_id": user_id, "display_title": display_title,
            "full_query": full_query, "pinned": False, "created_at": now, "updated_at": now}


def list_recent_queries(db_path, user_id: int) -> list[dict]:
    """Pinned items first (most recently updated first within each group),
    then unpinned items, most recent first."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT * FROM recent_queries WHERE user_id = ?
           ORDER BY pinned DESC, updated_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        # Stored as a JSON TEXT column — decode once here so the API
        # response carries a real array, not a double-encoded string.
        d["messages"] = json.loads(d.get("messages") or "[]")
        results.append(d)
    return results


def _get_owned_query(conn, query_id: int, user_id: int) -> dict | None:
    """Internal guard: every mutation must confirm the query actually belongs
    to the requesting user before touching it — otherwise user A could rename
    or delete user B's history by guessing an id."""
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM recent_queries WHERE id = ? AND user_id = ?", (query_id, user_id)
    ).fetchone()
    return dict(row) if row else None


def toggle_pin(db_path, query_id: int, user_id: int) -> dict:
    conn = sqlite3.connect(db_path)
    existing = _get_owned_query(conn, query_id, user_id)
    if not existing:
        conn.close()
        raise ValueError("Query not found or does not belong to this user.")

    new_pinned = 0 if existing["pinned"] else 1
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE recent_queries SET pinned = ?, updated_at = ? WHERE id = ?",
        (new_pinned, now, query_id),
    )
    conn.commit()
    conn.close()
    existing["pinned"] = bool(new_pinned)
    existing["updated_at"] = now
    return existing


def rename_query(db_path, query_id: int, user_id: int, new_title: str) -> dict:
    new_title = new_title.strip()
    if not new_title:
        raise ValueError("Title cannot be empty.")

    conn = sqlite3.connect(db_path)
    existing = _get_owned_query(conn, query_id, user_id)
    if not existing:
        conn.close()
        raise ValueError("Query not found or does not belong to this user.")

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE recent_queries SET display_title = ?, updated_at = ? WHERE id = ?",
        (new_title, now, query_id),
    )
    conn.commit()
    conn.close()
    existing["display_title"] = new_title
    existing["updated_at"] = now
    return existing


def clear_all(db_path, user_id: int) -> int:
    """Deletes every recent_queries row for this user — the "Clear
    conversation history" settings action. Returns the number of rows
    deleted so the caller/UI can confirm something actually happened."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("DELETE FROM recent_queries WHERE user_id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted


def delete_query(db_path, query_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(db_path)
    existing = _get_owned_query(conn, query_id, user_id)
    if not existing:
        conn.close()
        return False
    conn.execute("DELETE FROM recent_queries WHERE id = ?", (query_id,))
    conn.commit()
    conn.close()
    return True
