import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "viralens.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            input_type TEXT NOT NULL,
            input_preview TEXT,
            verdict TEXT,
            confidence INTEGER,
            result_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_check(result: dict, input_type: str = "text") -> int | None:
    if not result or not result.get("success"):
        return None

    reports = result.get("reports") or []
    first = reports[0] if reports else {}
    preview = result.get("input_text") or result.get("ocr_extracted_text") or ""
    preview = " ".join(preview.split())[:180]

    conn = _connect()
    cur = conn.execute(
        """
        INSERT INTO checks (created_at, input_type, input_preview, verdict, confidence, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            input_type,
            preview,
            first.get("verdict"),
            first.get("confidence"),
            json.dumps(result, ensure_ascii=False),
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def list_checks(limit: int = 20) -> list:
    init_db()
    conn = _connect()
    rows = conn.execute(
        """
        SELECT id, created_at, input_type, input_preview, verdict, confidence
        FROM checks
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_check(check_id: int) -> dict | None:
    conn = _connect()
    row = conn.execute(
        "SELECT result_json FROM checks WHERE id = ?",
        (check_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row["result_json"])
