from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from investment_analysis.cycles import build_position_cycles
from investment_analysis.compliance import compliance_guard
from investment_analysis.llm import summarize_behavior_segment, understand_answer
from investment_analysis.models import Trade
from investment_analysis.parser import parse_trade_file
from investment_analysis.questions import generate_questions
from investment_analysis.segments import detect_behavior_segments, select_representative_segments
from investment_analysis.storage import Repository
from investment_analysis.workflow import run_analysis


ROOT = Path(__file__).resolve().parents[1]


class CoreWorkflowTest(unittest.TestCase):
    def test_parse_and_build_cycles(self) -> None:
        trades, warnings, invalid = parse_trade_file(ROOT / "examples" / "trades.csv", "U001", "A001", "FILE_001")
        self.assertEqual(len(invalid), 0)
        self.assertGreaterEqual(len(trades), 10)
        self.assertIn("000001", {trade.symbol for trade in trades})
        self.assertTrue(any("手续费" in warning for warning in warnings) is False)
        cycles = build_position_cycles(trades, as_of=date(2025, 5, 7), account_asset=60000)
        self.assertGreaterEqual(len(cycles), 3)
        bank = next(cycle for cycle in cycles if cycle.symbol == "600000")
        self.assertEqual(bank.status, "OPEN")
        self.assertGreater(bank.max_position_weight, 0.5)

    def test_loss_averaging_and_concentration_segments(self) -> None:
        trades, _, _ = parse_trade_file(ROOT / "examples" / "trades.csv", "U001", "A001", "FILE_001")
        cycles = build_position_cycles(trades, as_of=date(2025, 5, 7), account_asset=60000)
        candidates = detect_behavior_segments(cycles, trades, as_of=date(2025, 5, 7))
        types = {segment.behavior_type for segment in candidates}
        self.assertIn("LOSS_AVERAGING_DOWN", types)
        self.assertIn("CONCENTRATION", types)
        selected = select_representative_segments(candidates)
        self.assertGreaterEqual(len(selected), 2)
        questions = generate_questions(selected)
        self.assertEqual(len(questions), min(15, len(selected) * 3))

    def test_end_to_end_report(self) -> None:
        result = run_analysis(
            user_id="U001",
            account_id="A001",
            trade_file_path=ROOT / "examples" / "trades.csv",
            source_file_id="FILE_001",
            account_asset=60000,
            holdings_rows=[
                {
                    "snapshot_date": "2025-05-07",
                    "user_id": "U001",
                    "account_id": "A001",
                    "symbol": "600000",
                    "stock_name": "示例银行",
                    "quantity": 3000,
                    "market_price": 7.8,
                    "market_value": 23400,
                    "position_weight": 0.39,
                    "unrealized_pnl": -2500,
                    "unrealized_pnl_pct": -0.1,
                    "sector": "金融",
                }
            ],
            answers=[
                {"question_id": "Q001", "selected_option": "A", "free_text": ""},
                {"question_id": "Q002", "selected_option": "C", "free_text": "当时想摊低成本回本"},
                {"question_id": "Q003", "selected_option": "B", "free_text": "仓位控制不合理"},
            ],
        )
        self.assertEqual(result["report"]["status"], "SUCCESS")
        self.assertIn("免责声明", result["report"]["markdown"])
        self.assertIsNotNone(result["suitability"])
        self.assertEqual(result["llm_enrichment"]["status"], "FALLBACK")
        self.assertGreaterEqual(len(result["llm_enrichment"]["behavior_summaries"]), 1)

    def test_llm_fallback_outputs_are_safe_and_structured(self) -> None:
        segment = {
            "segment_id": "SEG_001",
            "behavior_type": "LOSS_AVERAGING_DOWN",
            "symbol": "600000",
            "stock_name": "示例银行",
            "evidence": {
                "avg_down_count": 2,
                "max_position_weight": 0.31,
                "max_drawdown_pct": -0.22,
            },
        }
        summary = summarize_behavior_segment(segment)
        self.assertEqual(summary["segment_id"], "SEG_001")
        self.assertTrue(summary["compliance_passed"])
        self.assertIn("最高仓位", summary["behavior_observation"])

        understood = understand_answer({"question_id": "Q001", "selected_option": "C", "free_text": "当时想摊低成本回本，但没有明确计划"})
        labels = {item["label"] for item in understood["motives"]}
        self.assertIn("BREAKEVEN_MENTALITY", labels)
        self.assertIn("NO_CLEAR_PLAN", labels)
        self.assertLessEqual(abs(understood["persona_adjustments"]["discipline"]), 10)

        guarded = compliance_guard("建议卖出 A 股票，目标价 10 元。")
        self.assertFalse(guarded["passed"])
        self.assertNotIn("建议卖出", guarded["safe_version"])

    def test_verification_login_and_report_persistence(self) -> None:
        with TemporaryDirectory() as tmpdir:
            repo = Repository(Path(tmpdir) / "test.db")
            _, code = repo.create_verification_code("EMAIL", "demo@example.com")
            user = repo.verify_code_and_create_user("EMAIL", "demo@example.com", code)
            self.assertIsNotNone(user)
            session = repo.create_session(user["user_id"])
            session_user = repo.get_session_user(session["token"])
            self.assertEqual(session_user["user_id"], user["user_id"])

            repo.save_artifact("R_TEST", "REPORT", user["user_id"], "A001", {"report": {"summary": "测试报告"}, "markdown": "# 测试"})
            reports = repo.list_artifacts(user["user_id"])
            self.assertEqual(len(reports), 1)
            self.assertEqual(reports[0]["artifact_id"], "R_TEST")
            self.assertEqual(reports[0]["summary"], "测试报告")


class CycleAcceptanceTest(unittest.TestCase):
    def test_prd_cycle_acceptance_case(self) -> None:
        trades = [
            self.trade("2025-03-01", "BUY", 1000, 10),
            self.trade("2025-03-08", "BUY", 1000, 9),
            self.trade("2025-03-15", "SELL", 500, 11),
            self.trade("2025-04-01", "SELL", 1500, 12),
            self.trade("2025-05-01", "BUY", 1000, 8),
        ]
        cycles = build_position_cycles(trades, as_of=date(2025, 5, 7), account_asset=50000)
        self.assertEqual(len(cycles), 2)
        self.assertEqual(cycles[0].start_date, date(2025, 3, 1))
        self.assertEqual(cycles[0].end_date, date(2025, 4, 1))
        self.assertEqual(cycles[0].status, "CLOSED")
        self.assertEqual(cycles[1].start_date, date(2025, 5, 1))
        self.assertEqual(cycles[1].status, "OPEN")

    def trade(self, trade_date: str, side: str, quantity: float, price: float) -> Trade:
        from datetime import datetime

        return Trade(
            trade_id=f"{trade_date}-{side}",
            user_id="U001",
            account_id="A001",
            trade_date=datetime.fromisoformat(trade_date),
            symbol="A",
            stock_name="A 股票",
            side=side,
            quantity=quantity,
            price=price,
            gross_amount=quantity * price,
            source_file_id="FILE",
        )


if __name__ == "__main__":
    unittest.main()
