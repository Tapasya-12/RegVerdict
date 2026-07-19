"""
Authentication core: SQLite user storage (not the audit log's JSONL pattern —
credentials need real transactional guarantees, not an append-only text file),
bcrypt password hashing, JWT session tokens.

Deliberately NOT using passlib/python-jose to keep dependencies minimal and
avoid this project's recurring wheel/version-conflict history — bcrypt and
PyJWT are both simple, widely-used, and have prebuilt wheels for current
Python versions.
"""

import os
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "regverdict.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# In production this MUST come from an environment variable, never hardcoded.
# Falling back to a random-but-stable-per-process value for local dev only
# would invalidate all sessions on every restart, which is confusing — so
# instead we fail loudly if it's missing, forcing the .env to be set once.
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hour sessions


def _require_secret():
    if not SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. Add a long random string to your .env file — "
            "e.g. generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )


def init_db():
    """Creates all 4 tables that live in the shared regverdict.db: users
    (this module), audit_log (audit_log_sqlite.py), recent_queries
    (recent_queries.py), and documents (the document_manifest.json
    migration). One init_db() call at API startup owns the whole schema so
    none of the other modules need their own CREATE TABLE — they just
    assume these exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            tool TEXT NOT NULL,
            policy_text TEXT,
            proposed_change TEXT,
            verdict TEXT,
            confidence REAL,
            document_name TEXT,
            clause_number TEXT,
            grounding_verified INTEGER,
            status_flipped INTEGER,
            timestamp TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS recent_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            display_title TEXT NOT NULL,
            full_query TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # document_name is the manifest key (e.g. "rbi_kyc_master_direction"),
    # not a surrogate id — every other table in this app already addresses
    # documents by that same string, so this avoids a join just to resolve one.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_name TEXT PRIMARY KEY,
            regulator TEXT NOT NULL,
            effective_date TEXT,
            topic_tags TEXT,
            supersedes_clause_id TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_user(username: str, email: str, password: str) -> dict:
    """Raises ValueError with a user-facing message on duplicate username/email
    or weak password — caller (the API endpoint) should catch this and return
    a 400, not a 500."""
    username = username.strip()
    email = email.strip().lower()

    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "username": username, "email": email}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            raise ValueError(f"Username '{username}' is already taken.")
        elif "email" in str(e):
            raise ValueError(f"An account with email '{email}' already exists.")
        raise ValueError("Could not create account — username or email already in use.")
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict | None:
    """Returns the user dict (without password_hash) if credentials are valid, else None.
    Deliberately does NOT distinguish "user doesn't exist" from "wrong password" in its
    return value — that distinction should never leak to the API response, since it
    tells an attacker whether a username is registered."""
    user = get_user_by_username(username)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return None
    return {"id": user["id"], "username": user["username"], "email": user["email"]}


def create_access_token(username: str) -> str:
    _require_secret()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Returns the username if the token is valid and unexpired.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError otherwise —
    caller (the FastAPI dependency) should catch both and return 401."""
    _require_secret()
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload["sub"]
