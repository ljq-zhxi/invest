from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .cycles import build_position_cycles
from .llm import build_llm_enrichment
from .parser import normalize_holdings, normalize_market_data, parse_trade_file
from .persona import generate_persona
from .questions import generate_questions
from .report import generate_report
from .segments import detect_behavior_segments, select_representative_segments
from .suitability import analyze_suitability
from .utils import dataclass_to_dict


def run_analysis(
    user_id: str,
    account_id: str,
    trade_file_path: str | Path,
    source_file_id: str = "FILE_001",
    field_mapping: dict[str, str] | None = None,
    holdings_rows: list[dict[str, Any]] | None = None,
    market_rows: list[dict[str, Any]] | None = None,
    answers: list[dict[str, str]] | None = None,
    account_asset: float | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    trades, warnings, invalid_rows = parse_trade_file(trade_file_path, user_id, account_id, source_file_id, field_mapping)
    holdings = normalize_holdings(holdings_rows or [])
    market_data = normalize_market_data(market_rows or [])
    cycles = build_position_cycles(trades, as_of=as_of, account_asset=account_asset)
    candidates = detect_behavior_segments(cycles, trades, market_data, holdings, as_of=as_of)
    selected = select_representative_segments(candidates)
    questions = generate_questions(selected)
    persona = generate_persona(user_id, account_id, selected, questions, answers or [])
    suitability = analyze_suitability(user_id, account_id, persona, holdings, selected) if holdings else None
    report = generate_report(persona, selected, questions, answers or [], suitability)
    result = dataclass_to_dict(
        {
            "parse_result": {
                "status": "SUCCESS" if trades else "FAILED",
                "total_rows": len(trades) + len(invalid_rows),
                "valid_rows": len(trades),
                "invalid_rows": len(invalid_rows),
                "warnings": warnings,
                "invalid_row_details": invalid_rows,
            },
            "normalized_trades": trades,
            "position_cycles": cycles,
            "candidate_segments": candidates,
            "selected_segments": selected,
            "questions": questions,
            "answers": answers or [],
            "persona": persona,
            "suitability": suitability,
            "report": report,
        }
    )
    result["llm_enrichment"] = build_llm_enrichment(result)
    return result
