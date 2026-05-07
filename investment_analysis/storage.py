from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
  source_file_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_type TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL,
  user_id TEXT NOT NULL,
  account_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Repository:
    def __init__(self, db_path: str | Path = "investment_analysis.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_upload(self, source_file_id: str, user_id: str, account_id: str, file_name: str, file_path: str, file_type: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO uploads(source_file_id, user_id, account_id, file_name, file_path, file_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (source_file_id, user_id, account_id, file_name, file_path, file_type, "SUCCESS"),
            )

    def get_upload(self, source_file_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM uploads WHERE source_file_id = ?", (source_file_id,)).fetchone()
        return dict(row) if row else None

    def save_artifact(self, artifact_id: str, artifact_type: str, user_id: str, account_id: str, payload: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifacts(artifact_id, artifact_type, user_id, account_id, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (artifact_id, artifact_type, user_id, account_id, json.dumps(payload, ensure_ascii=False)),
            )

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result
