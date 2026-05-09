from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .llm import (
    MODEL_NAME,
    PROMPT_VERSION,
    generate_segment_questions,
    summarize_behavior_segment,
    understand_answer,
    write_report_sections,
)
from .compliance import compliance_guard
from .parser import infer_field_mapping, read_tabular_file
from .storage import Repository
from .workflow import run_analysis


class AppState:
    def __init__(self, db_path: str | Path) -> None:
        self.repo = Repository(db_path)


class InvestmentAnalysisHandler(BaseHTTPRequestHandler):
    server_version = "InvestmentAnalysis/0.1"

    @property
    def state(self) -> AppState:
        return self.server.state  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.serve_static_file("index.html")
            return
        if parsed.path.startswith("/static/"):
            self.serve_static_file(parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/health":
            self.respond({"status": "ok"})
            return
        if parsed.path == "/api/v1/me":
            self.handle_me()
            return
        if parsed.path == "/api/v1/reports":
            self.handle_list_reports()
            return
        if parsed.path.startswith("/api/v1/trades/parse-result/"):
            artifact_id = parsed.path.rsplit("/", 1)[-1]
            artifact = self.state.repo.get_artifact(artifact_id)
            if not artifact:
                self.error(HTTPStatus.NOT_FOUND, "parse result not found")
                return
            self.respond(artifact["payload"]["parse_result"])
            return
        if parsed.path.startswith("/reports/"):
            artifact_id = parsed.path.rsplit("/", 1)[-1]
            artifact = self.state.repo.get_artifact(artifact_id)
            if not artifact:
                self.error(HTTPStatus.NOT_FOUND, "report not found")
                return
            if artifact_id != "R_001":
                user = self.current_user(allow_query_token=True)
                if not user or user["user_id"] != artifact["user_id"]:
                    self.error(HTTPStatus.UNAUTHORIZED, "login required")
                    return
            markdown = artifact["payload"].get("markdown", "")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.end_headers()
            self.wfile.write(markdown.encode("utf-8"))
            return
        self.error(HTTPStatus.NOT_FOUND, "route not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self.read_json()
        try:
            if parsed.path == "/api/v1/auth/request-code":
                self.handle_request_code(payload)
            elif parsed.path == "/api/v1/auth/verify-code":
                self.handle_verify_code(payload)
            elif parsed.path == "/api/v1/uploads/trade-statement":
                self.handle_upload(payload)
            elif parsed.path == "/api/v1/trades/parse":
                self.handle_parse(payload)
            elif parsed.path == "/api/v1/analysis/run":
                self.handle_run_analysis(payload)
            elif parsed.path == "/api/v1/reports/generate":
                self.handle_report(payload)
            elif parsed.path == "/api/v1/llm/behavior-summary":
                self.handle_llm_behavior_summary(payload)
            elif parsed.path == "/api/v1/llm/questions/generate":
                self.handle_llm_questions(payload)
            elif parsed.path == "/api/v1/llm/answers/understand":
                self.handle_llm_answer_understanding(payload)
            elif parsed.path == "/api/v1/llm/reports/write":
                self.handle_llm_report_write(payload)
            elif parsed.path == "/api/v1/llm/compliance/check":
                self.handle_llm_compliance_check(payload)
            else:
                self.error(HTTPStatus.NOT_FOUND, "route not found")
        except Exception as exc:
            self.error(HTTPStatus.BAD_REQUEST, str(exc))

    def handle_request_code(self, payload: dict[str, Any]) -> None:
        contact = str(payload.get("contact") or "").strip().lower()
        if not contact:
            raise ValueError("contact is required")
        contact_type = self.contact_type(contact)
        code_id, code = self.state.repo.create_verification_code(contact_type, contact)
        self.respond({
            "code_id": code_id,
            "contact_type": contact_type,
            "contact": contact,
            "expires_in_seconds": 600,
            "dev_code": code,
            "message": "验证码已生成。当前本地版本直接返回 dev_code，接入短信或邮件服务后可去掉该字段。",
        })

    def handle_verify_code(self, payload: dict[str, Any]) -> None:
        contact = str(payload.get("contact") or "").strip().lower()
        code = str(payload.get("code") or "").strip()
        if not contact or not code:
            raise ValueError("contact and code are required")
        contact_type = self.contact_type(contact)
        user = self.state.repo.verify_code_and_create_user(contact_type, contact, code)
        if not user:
            self.error(HTTPStatus.UNAUTHORIZED, "invalid or expired verification code")
            return
        session = self.state.repo.create_session(user["user_id"])
        self.respond({"user": user, **session})

    def handle_me(self) -> None:
        user = self.current_user()
        if not user:
            self.error(HTTPStatus.UNAUTHORIZED, "login required")
            return
        self.respond({"user": user})

    def handle_list_reports(self) -> None:
        user = self.current_user()
        if not user:
            self.error(HTTPStatus.UNAUTHORIZED, "login required")
            return
        reports = self.state.repo.list_artifacts(user["user_id"], "REPORT")
        token = self.auth_token()
        for report in reports:
            if report["artifact_id"] != "R_001" and token:
                report["report_url"] = f"/reports/{report['artifact_id']}?token={token}"
        self.respond({"reports": reports})

    def handle_upload(self, payload: dict[str, Any]) -> None:
        file_path = str(payload.get("file_path") or "")
        if not file_path:
            raise ValueError("file_path is required for the stdlib API server")
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"file not found: {file_path}")
        user_id = str(payload["user_id"])
        account_id = str(payload["account_id"])
        file_name = str(payload.get("file_name") or path.name)
        file_type = str(payload.get("file_type") or path.suffix.lstrip("."))
        seed = "|".join([user_id, account_id, str(path.resolve())])
        source_file_id = "FILE_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10].upper()
        self.state.repo.save_upload(source_file_id, user_id, account_id, file_name, str(path), file_type)
        rows = read_tabular_file(path)
        self.respond({"source_file_id": source_file_id, "upload_status": "SUCCESS", "suggested_field_mapping": infer_field_mapping(list(rows[0].keys()) if rows else [])})

    def handle_parse(self, payload: dict[str, Any]) -> None:
        upload = self.state.repo.get_upload(str(payload["source_file_id"]))
        if not upload:
            raise ValueError("source_file_id not found")
        result = run_analysis(
            user_id=upload["user_id"],
            account_id=upload["account_id"],
            trade_file_path=upload["file_path"],
            source_file_id=upload["source_file_id"],
            field_mapping=payload.get("field_mapping"),
            holdings_rows=payload.get("current_holdings") or [],
            market_rows=payload.get("market_data") or [],
            answers=payload.get("answers") or [],
            account_asset=payload.get("account_asset"),
        )
        parse_job_id = "JOB_" + upload["source_file_id"].replace("FILE_", "")
        self.state.repo.save_artifact(parse_job_id, "ANALYSIS", upload["user_id"], upload["account_id"], result)
        self.respond({"parse_job_id": parse_job_id, "status": "SUCCESS", "warnings": result["parse_result"]["warnings"]})

    def handle_run_analysis(self, payload: dict[str, Any]) -> None:
        user = self.current_user(required=False)
        request_user_id = user["user_id"] if user else str(payload["user_id"])
        contact_account = user["contact"] if user else str(payload["account_id"])
        account_id = str(payload.get("account_id") or contact_account)
        result = run_analysis(
            user_id=request_user_id,
            account_id=account_id,
            trade_file_path=str(payload["trade_file_path"]),
            source_file_id=str(payload.get("source_file_id") or "FILE_DIRECT"),
            field_mapping=payload.get("field_mapping"),
            holdings_rows=payload.get("current_holdings") or [],
            market_rows=payload.get("market_data") or [],
            answers=payload.get("answers") or [],
            account_asset=payload.get("account_asset"),
        )
        if user:
            suffix = hashlib.sha1(f"{user['user_id']}:{account_id}:{json.dumps(result['parse_result'], sort_keys=True)}:{hashlib.sha1(json.dumps(result, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()}".encode("utf-8")).hexdigest()[:12].upper()
            analysis_id = "JOB_" + suffix
            report_id = "R_" + suffix
            result["analysis_id"] = analysis_id
            result["report_id"] = report_id
            result["report_url"] = f"/reports/{report_id}"
            self.state.repo.save_artifact(analysis_id, "ANALYSIS", user["user_id"], account_id, result)
            self.state.repo.save_artifact(report_id, "REPORT", user["user_id"], account_id, result["report"])
        else:
            self.state.repo.save_artifact("JOB_DIRECT", "ANALYSIS", request_user_id, account_id, result)
            self.state.repo.save_artifact("R_001", "REPORT", request_user_id, account_id, result["report"])
            result["analysis_id"] = "JOB_DIRECT"
            result["report_id"] = "R_001"
            result["report_url"] = "/reports/R_001"
        self.respond(result)

    def handle_report(self, payload: dict[str, Any]) -> None:
        artifact = self.state.repo.get_artifact(str(payload.get("parse_job_id") or "JOB_DIRECT"))
        if not artifact:
            raise ValueError("analysis artifact not found")
        report_payload = artifact["payload"]["report"]
        self.state.repo.save_artifact("R_001", "REPORT", artifact["user_id"], artifact["account_id"], report_payload)
        self.respond({"report_id": "R_001", "status": "SUCCESS", "report_url": "/reports/R_001"})

    def handle_llm_behavior_summary(self, payload: dict[str, Any]) -> None:
        artifact = self.get_analysis_artifact(payload)
        segment = self.find_segment(artifact["payload"], str(payload["segment_id"]))
        output = summarize_behavior_segment(segment)
        task_id = self.save_llm_task(artifact, "SUMMARY", payload, output)
        self.respond({"llm_task_id": task_id, **output})

    def handle_llm_questions(self, payload: dict[str, Any]) -> None:
        artifact = self.get_analysis_artifact(payload)
        segment_ids = payload.get("segment_ids") or []
        if not segment_ids:
            raise ValueError("segment_ids is required")
        count = int(payload.get("question_count_per_segment") or 3)
        outputs = [
            generate_segment_questions(self.find_segment(artifact["payload"], str(segment_id)), count)
            for segment_id in segment_ids
        ]
        questions = []
        for item in outputs:
            for question in item["questions"]:
                questions.append({"segment_id": item["segment_id"], **question})
        output = {"questionnaire_id": "Q_001", "questions": questions, "compliance_passed": all(item["compliance_passed"] for item in outputs), "source": MODEL_NAME}
        task_id = self.save_llm_task(artifact, "QUESTION", payload, output)
        self.respond({"llm_task_id": task_id, **output})

    def handle_llm_answer_understanding(self, payload: dict[str, Any]) -> None:
        artifact = self.get_analysis_artifact(payload, required=False)
        question = None
        if artifact:
            question_id = str(payload.get("question_id") or "")
            question = next((item for item in artifact["payload"].get("questions", []) if item.get("question_id") == question_id), None)
        output = understand_answer(payload, question)
        user_id = artifact["user_id"] if artifact else str(payload.get("user_id") or "UNKNOWN")
        task_id = self.state.repo.save_llm_task(user_id, "ANSWER_UNDERSTANDING", payload, output, MODEL_NAME, PROMPT_VERSION)
        answer_id = str(payload.get("question_id") or task_id)
        label_ids = self.state.repo.save_answer_motive_labels(answer_id, output["motives"], output["source"])
        self.respond({"llm_task_id": task_id, "motive_label_ids": label_ids, **output})

    def handle_llm_report_write(self, payload: dict[str, Any]) -> None:
        artifact = self.get_analysis_artifact(payload)
        output = write_report_sections(artifact["payload"])
        task_id = self.save_llm_task(artifact, "REPORT", payload, output)
        self.respond({"llm_task_id": task_id, **output})

    def handle_llm_compliance_check(self, payload: dict[str, Any]) -> None:
        text = str(payload.get("text") or "")
        if not text:
            raise ValueError("text is required")
        output = compliance_guard(text)
        user_id = str(payload.get("user_id") or "UNKNOWN")
        task_id = self.state.repo.save_llm_task(user_id, "COMPLIANCE", payload, output, MODEL_NAME, PROMPT_VERSION)
        result_id = self.state.repo.save_llm_compliance_result(task_id, bool(output["passed"]), output["violations"], str(output["safe_version"]))
        self.respond({"llm_task_id": task_id, "compliance_result_id": result_id, **output})

    def get_analysis_artifact(self, payload: dict[str, Any], required: bool = True) -> dict[str, Any] | None:
        artifact_id = str(payload.get("parse_job_id") or "JOB_DIRECT")
        artifact = self.state.repo.get_artifact(artifact_id)
        if not artifact and required:
            raise ValueError("analysis artifact not found")
        return artifact

    def find_segment(self, analysis_payload: dict[str, Any], segment_id: str) -> dict[str, Any]:
        for key in ("selected_segments", "candidate_segments"):
            for segment in analysis_payload.get(key, []):
                if segment.get("segment_id") == segment_id:
                    return segment
        raise ValueError("segment_id not found")

    def save_llm_task(self, artifact: dict[str, Any], task_type: str, input_payload: dict[str, Any], output_payload: dict[str, Any]) -> str:
        return self.state.repo.save_llm_task(
            artifact["user_id"],
            task_type,
            input_payload,
            output_payload,
            MODEL_NAME,
            PROMPT_VERSION,
        )

    def serve_static_file(self, relative_path: str) -> None:
        static_root = Path(__file__).resolve().parent / "static"
        target = (static_root / relative_path).resolve()
        if static_root not in target.parents and target != static_root:
            self.error(HTTPStatus.NOT_FOUND, "route not found")
            return
        if not target.exists() or not target.is_file():
            self.error(HTTPStatus.NOT_FOUND, "route not found")
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def current_user(self, required: bool = False, allow_query_token: bool = False) -> dict[str, Any] | None:
        token = self.auth_token(allow_query_token)
        user = self.state.repo.get_session_user(token) if token else None
        if required and not user:
            raise ValueError("login required")
        return user

    def auth_token(self, allow_query_token: bool = False) -> str:
        header = self.headers.get("Authorization", "")
        if header.lower().startswith("bearer "):
            return header.split(" ", 1)[1].strip()
        if allow_query_token:
            parsed = urlparse(self.path)
            query = dict(part.split("=", 1) for part in parsed.query.split("&") if "=" in part)
            return query.get("token", "")
        return ""

    def contact_type(self, contact: str) -> str:
        if "@" in contact:
            return "EMAIL"
        digits = "".join(ch for ch in contact if ch.isdigit())
        if len(digits) >= 6:
            return "PHONE"
        raise ValueError("contact must be an email or phone number")

    def respond(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def error(self, status: HTTPStatus, message: str) -> None:
        self.respond({"error": message}, status)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8000, db_path: str = "investment_analysis.db") -> None:
    server = ThreadingHTTPServer((host, port), InvestmentAnalysisHandler)
    server.state = AppState(db_path)  # type: ignore[attr-defined]
    print(f"Investment analysis service listening on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI investment persona and suitability analysis service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="investment_analysis.db")
    args = parser.parse_args()
    serve(args.host, args.port, args.db)


if __name__ == "__main__":
    main()
