"""
One-time migration: copies every entry in data/document_manifest.json into
the new `documents` table in data/regverdict.db.

Run once, after auth.init_db() has created the schema:
    venv/Scripts/python.exe api/migrate_documents.py

data/document_manifest.json remains the source of truth for
ingestion/embed_and_load.py (which still reads it directly at ingest time —
see the MANIFEST_PATH constant there) — this script only mirrors it into the
database for the API to query. Re-running is safe: existing rows are
upserted, not duplicated.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth  # noqa: E402

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "document_manifest.json"


def migrate():
    auth.init_db()

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    conn = sqlite3.connect(auth.DB_PATH)
    inserted = 0
    for document_name, entry in manifest.items():
        if document_name.startswith("_"):
            continue  # skip _comment / _example
        conn.execute(
            """INSERT INTO documents (document_name, regulator, effective_date, topic_tags, supersedes_clause_id)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(document_name) DO UPDATE SET
                   regulator=excluded.regulator,
                   effective_date=excluded.effective_date,
                   topic_tags=excluded.topic_tags,
                   supersedes_clause_id=excluded.supersedes_clause_id""",
            (
                document_name,
                entry.get("regulator"),
                entry.get("effective_date"),
                json.dumps(entry.get("topic_tags", [])),
                entry.get("supersedes_clause_id") or None,
            ),
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"Migrated {inserted} document(s) from {MANIFEST_PATH.name} into {auth.DB_PATH.name}")


if __name__ == "__main__":
    migrate()
