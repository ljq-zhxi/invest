from __future__ import annotations

import argparse
import hashlib
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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
        if parsed.path == "/health":
            self.respond({"status": "ok"})
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
            if parsed.path == "/api/v1/uploads/trade-statement":
                self.handle_upload(payload)
            elif parsed.path == "/api/v1/trades/parse":
                self.handle_parse(payload)
            elif parsed.path == "/api/v1/analysis/run":
                self.handle_run_analysis(payload)
            elif parsed.path == "/api/v1/reports/generate":
                self.handle_report(payload)
            else:
                self.error(HTTPStatus.NOT_FOUND, "route not found")
        except Exception as exc:
            self.error(HTTPStatus.BAD_REQUEST, str(exc))

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
        result = run_analysis(
            user_id=str(payload["user_id"]),
            account_id=str(payload["account_id"]),
            trade_file_path=str(payload["trade_file_path"]),
            source_file_id=str(payload.get("source_file_id") or "FILE_DIRECT"),
            field_mapping=payload.get("field_mapping"),
            holdings_rows=payload.get("current_holdings") or [],
            market_rows=payload.get("market_data") or [],
            answers=payload.get("answers") or [],
            account_asset=payload.get("account_asset"),
        )
        self.state.repo.save_artifact("JOB_DIRECT", "ANALYSIS", str(payload["user_id"]), str(payload["account_id"]), result)
        self.state.repo.save_artifact("R_001", "REPORT", str(payload["user_id"]), str(payload["account_id"]), result["report"])
        self.respond(result)

    def handle_report(self, payload: dict[str, Any]) -> None:
        artifact = self.state.repo.get_artifact(str(payload.get("parse_job_id") or "JOB_DIRECT"))
        if not artifact:
            raise ValueError("analysis artifact not found")
        report_payload = artifact["payload"]["report"]
        self.state.repo.save_artifact("R_001", "REPORT", artifact["user_id"], artifact["account_id"], report_payload)
        self.respond({"report_id": "R_001", "status": "SUCCESS", "report_url": "/reports/R_001"})

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

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
