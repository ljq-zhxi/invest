from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import UTC, datetime, timedelta
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
CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  contact_type TEXT NOT NULL,
  contact TEXT NOT NULL UNIQUE,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  last_login_at TEXT
);
CREATE TABLE IF NOT EXISTS verification_codes (
  code_id TEXT PRIMARY KEY,
  contact_type TEXT NOT NULL,
  contact TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  consumed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS llm_tasks (
  llm_task_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  task_type TEXT NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT NOT NULL,
  model_name TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS llm_compliance_results (
  compliance_result_id TEXT PRIMARY KEY,
  llm_task_id TEXT NOT NULL,
  passed INTEGER NOT NULL,
  violations_json TEXT NOT NULL,
  safe_version TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS answer_motive_labels (
  label_id TEXT PRIMARY KEY,
  answer_id TEXT NOT NULL,
  motive_label TEXT NOT NULL,
  confidence REAL NOT NULL,
  source TEXT NOT NULL,
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

    def list_artifacts(self, user_id: str, artifact_type: str = "REPORT", limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT artifact_id, artifact_type, user_id, account_id, payload_json, created_at
                FROM artifacts
                WHERE user_id = ? AND artifact_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, artifact_type, limit),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            payload = json.loads(item.pop("payload_json"))
            report = payload.get("report", {}) if isinstance(payload, dict) else {}
            item["summary"] = report.get("summary") or payload.get("summary") or ""
            item["report_url"] = f"/reports/{item['artifact_id']}"
            items.append(item)
        return items

    def create_verification_code(self, contact_type: str, contact: str, ttl_minutes: int = 10) -> tuple[str, str]:
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_id = "VC_" + secrets.token_hex(8).upper()
        code_hash = self._hash_secret(code)
        expires_at = (datetime.now(UTC) + timedelta(minutes=ttl_minutes)).isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO verification_codes(code_id, contact_type, contact, code_hash, expires_at, consumed)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (code_id, contact_type, contact, code_hash, expires_at),
            )
        return code_id, code

    def verify_code_and_create_user(self, contact_type: str, contact: str, code: str) -> dict[str, Any] | None:
        now = datetime.now(UTC).isoformat()
        code_hash = self._hash_secret(code)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM verification_codes
                WHERE contact_type = ? AND contact = ? AND code_hash = ? AND consumed = 0 AND expires_at > ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (contact_type, contact, code_hash, now),
            ).fetchone()
            if not row:
                return None
            conn.execute("UPDATE verification_codes SET consumed = 1 WHERE code_id = ?", (row["code_id"],))
            user = conn.execute("SELECT * FROM users WHERE contact = ?", (contact,)).fetchone()
            if user:
                user_id = user["user_id"]
                conn.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
            else:
                user_id = "U_" + hashlib.sha1(f"{contact_type}:{contact}".encode("utf-8")).hexdigest()[:12].upper()
                conn.execute(
                    """
                    INSERT INTO users(user_id, contact_type, contact, last_login_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, contact_type, contact),
                )
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(user) if user else None

    def create_session(self, user_id: str, ttl_days: int = 7) -> dict[str, Any]:
        token = "tok_" + secrets.token_urlsafe(32)
        expires_at = (datetime.now(UTC) + timedelta(days=ttl_days)).isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sessions(token, user_id, expires_at) VALUES (?, ?, ?)",
                (token, user_id, expires_at),
            )
        return {"token": token, "expires_at": expires_at}

    def get_session_user(self, token: str) -> dict[str, Any] | None:
        if not token:
            return None
        now = datetime.now(UTC).isoformat()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT users.*
                FROM sessions
                JOIN users ON users.user_id = sessions.user_id
                WHERE sessions.token = ? AND sessions.expires_at > ?
                """,
                (token, now),
            ).fetchone()
        return dict(row) if row else None

    def _hash_secret(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def save_llm_task(
        self,
        user_id: str,
        task_type: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        model_name: str,
        prompt_version: str,
        status: str = "FALLBACK",
        error_message: str = "",
    ) -> str:
        seed = json.dumps(
            {
                "user_id": user_id,
                "task_type": task_type,
                "input": input_payload,
                "output": output_payload,
                "status": status,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        task_id = "LLM_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12].upper()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO llm_tasks(
                  llm_task_id, user_id, task_type, input_json, output_json,
                  model_name, prompt_version, status, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    user_id,
                    task_type,
                    json.dumps(input_payload, ensure_ascii=False),
                    json.dumps(output_payload, ensure_ascii=False),
                    model_name,
                    prompt_version,
                    status,
                    error_message,
                ),
            )
        return task_id

    def save_llm_compliance_result(self, llm_task_id: str, passed: bool, violations: list[dict[str, Any]], safe_version: str) -> str:
        seed = json.dumps({"task": llm_task_id, "passed": passed, "safe": safe_version}, ensure_ascii=False, sort_keys=True)
        result_id = "LCR_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12].upper()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO llm_compliance_results(
                  compliance_result_id, llm_task_id, passed, violations_json, safe_version
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (result_id, llm_task_id, int(passed), json.dumps(violations, ensure_ascii=False), safe_version),
            )
        return result_id

    def save_answer_motive_labels(self, answer_id: str, motives: list[dict[str, Any]], source: str) -> list[str]:
        label_ids: list[str] = []
        with self.connect() as conn:
            for motive in motives:
                label = str(motive.get("label") or "UNCERTAIN")
                confidence = float(motive.get("confidence") or 0.0)
                seed = json.dumps({"answer_id": answer_id, "label": label, "confidence": confidence, "source": source}, sort_keys=True)
                label_id = "AML_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12].upper()
                conn.execute(
                    """
                    INSERT OR REPLACE INTO answer_motive_labels(
                      label_id, answer_id, motive_label, confidence, source
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (label_id, answer_id, label, confidence, source),
                )
                label_ids.append(label_id)
        return label_ids
