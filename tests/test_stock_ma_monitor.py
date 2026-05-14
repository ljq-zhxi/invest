from __future__ import annotations

import unittest

from stock_ma_monitor import (
    DailyBar,
    analyze_drawdown_from_recent_peak,
    analyze_trend_retracement_and_break,
    calculate_ma,
    ma_position_status,
    overall_status,
)


class StockMaMonitorTest(unittest.TestCase):
    def test_calculate_ma_uses_latest_n_closes(self) -> None:
        bars = [
            DailyBar(str(index), 0, 0, 0, float(index), 0)
            for index in range(1, 11)
        ]

        ma = calculate_ma(bars, [5, 10, 20])

        self.assertEqual(ma[5], 8.0)
        self.assertEqual(ma[10], 5.5)
        self.assertIsNone(ma[20])

    def test_ma_position_status(self) -> None:
        self.assertEqual(ma_position_status(101, 100, 0.3, 20), ("20日线上", 1.0))
        self.assertEqual(ma_position_status(99.5, 100, 0.3, 20), ("20日线下", -0.5))
        self.assertEqual(ma_position_status(100.2, 100, 0.3, 20), ("贴近20日线", 0.2))

    def test_overall_status(self) -> None:
        self.assertEqual(overall_status(120, {5: 110, 10: 105, 20: 100, 30: 95, 60: 90}), "强多头")
        self.assertEqual(overall_status(80, {5: 90, 10: 95, 20: 100, 30: 105, 60: 110}), "强空头")
        self.assertEqual(overall_status(106, {5: 101, 10: 102, 20: 100, 30: 104, 60: 99}), "偏多")
        self.assertEqual(overall_status(99, {5: 101, 10: 102, 20: 100, 30: 98, 60: 100}), "偏空")
        self.assertEqual(overall_status(100, {5: 101, 10: 99, 20: 100, 30: 98, 60: 97}), "震荡")
        self.assertEqual(overall_status(100, {5: 101, 10: 99, 20: None, 30: 98, 60: 97}), "数据不足")

    def test_analyze_trend_retracement_and_break(self) -> None:
        bars = [
            DailyBar("2026-01-01", 10, 10.5, 9.9, 10.0, 1000),
            DailyBar("2026-01-02", 10.1, 10.6, 10.0, 10.3, 1000),
            DailyBar("2026-01-03", 10.2, 10.7, 10.1, 10.6, 1000),
            DailyBar("2026-01-04", 10.4, 10.9, 10.3, 10.8, 1000),
            DailyBar("2026-01-05", 10.5, 11.0, 10.4, 10.9, 1000),
            DailyBar("2026-01-06", 10.6, 10.8, 10.2, 10.3, 1000),
            DailyBar("2026-01-07", 10.4, 10.5, 9.8, 10.0, 1000),
            DailyBar("2026-01-08", 10.2, 10.3, 9.6, 9.8, 1000),
            DailyBar("2026-01-09", 10.0, 10.1, 9.3, 9.5, 1000),
            DailyBar("2026-01-10", 9.8, 9.9, 9.1, 9.2, 1000),
        ]

        analysis = analyze_trend_retracement_and_break(bars, [5])

        self.assertIn("summary", analysis)
        self.assertIn("logs", analysis)
        self.assertIn("统计", analysis["summary"])
        self.assertTrue(len(analysis["logs"]) > 0)

    def test_analyze_drawdown_from_recent_peak(self) -> None:
        bars = [
            DailyBar("2026-01-01", 10, 10.5, 9.9, 10.0, 1000),
            DailyBar("2026-01-02", 10.4, 10.8, 10.3, 10.6, 1000),
            DailyBar("2026-01-03", 10.9, 11.2, 10.8, 11.0, 1000),
            DailyBar("2026-01-04", 10.7, 10.8, 10.2, 10.4, 1000),
            DailyBar("2026-01-05", 10.5, 10.6, 10.0, 10.2, 1000),
        ]

        analysis = analyze_drawdown_from_recent_peak(bars)

        self.assertEqual(analysis["peak_date"], "2026-01-03")
        self.assertLess(analysis["diff_pct"], 0)
        self.assertIn("下跌", analysis["summary"])


if __name__ == "__main__":
    unittest.main()
