from __future__ import annotations

import unittest

from stock_ma_monitor import DailyBar, calculate_ma, ma_position_status, overall_status


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


if __name__ == "__main__":
    unittest.main()
