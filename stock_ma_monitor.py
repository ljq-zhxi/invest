#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

DEFAULT_CONFIG = {
    "ma_windows": [5, 10, 20, 30, 60],
    "near_threshold_pct": 0.3,
    "output_path": "output/a_stock_ma_report.html",
    "request_timeout_seconds": 10,
    "retry_times": 3,
    "history_limit": "all",
}


@dataclass(slots=True)
class Stock:
    code: str
    name: str = ""
    market: str = ""


@dataclass(slots=True)
class DailyBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockDataSource:
    name = "unknown"

    def get_daily_bars(self, code: str, market: str, limit: int = 80) -> list[DailyBar]:
        raise NotImplementedError

    def _fetch(self, url: str, timeout: int) -> str:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="ignore")


class TencentDataSource(StockDataSource):
    name = "腾讯财经(前复权)"

    def __init__(self, timeout_seconds: int = 10, retry_times: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_times = retry_times

    def get_daily_bars(self, code: str, market: str, limit: int = 80) -> list[DailyBar]:
        symbol = f"{market}{code}"
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{limit},qfq"

        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            try:
                payload = self._fetch(url, self.timeout_seconds)
                return self._parse_payload(payload, symbol)
            except Exception as exc:
                last_error = exc
                logging.debug("Tencent fetch failed: symbol=%s attempt=%s error=%s", symbol, attempt, exc)
            if attempt < self.retry_times:
                time.sleep(min(2, attempt))
        raise RuntimeError(f"Tencent API Error: {last_error}")

    def _parse_payload(self, payload: str, symbol: str) -> list[DailyBar]:
        data = json.loads(payload)
        if data.get("code") != 0:
            return []
        klines = data.get("data", {}).get(symbol, {})
        day_data = klines.get("qfqday") or klines.get("day") or []
        bars: list[DailyBar] = []
        for item in day_data:
            if not isinstance(item, list) or len(item) < 6: continue
            day = str(item[0]).strip()
            close = to_float(item[2])
            if not day or close <= 0: continue
            bars.append(
                DailyBar(
                    date=day, open=to_float(item[1]), close=close,
                    high=to_float(item[3]), low=to_float(item[4]), volume=to_float(item[5]),
                )
            )
        bars.sort(key=lambda bar: bar.date)
        return bars


class EastMoneyDataSource(StockDataSource):
    """东方财富数据源 - 完美支持前复权，作为高可靠的备用源"""
    name = "东方财富(前复权)"

    def __init__(self, timeout_seconds: int = 10, retry_times: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_times = retry_times

    def get_daily_bars(self, code: str, market: str, limit: int = 80) -> list[DailyBar]:
        market_id = "1" if market == "sh" else "0"
        secid = f"{market_id}.{code}"
        # klt=101为日线, fqt=1为前复权
        url = f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56&klt=101&fqt=1&end=20500101&lmt={limit}"

        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            try:
                payload = self._fetch(url, self.timeout_seconds)
                data = json.loads(payload)
                if not data or not data.get("data") or not data["data"].get("klines"):
                    return []
                bars: list[DailyBar] = []
                for kline in data["data"]["klines"]:
                    parts = kline.split(",")
                    if len(parts) >= 6:
                        bars.append(DailyBar(
                            date=parts[0],
                            open=to_float(parts[1]),
                            close=to_float(parts[2]),
                            high=to_float(parts[3]),
                            low=to_float(parts[4]),
                            volume=to_float(parts[5])
                        ))
                return bars
            except Exception as exc:
                last_error = exc
                logging.debug("EastMoney fetch failed: symbol=%s attempt=%s error=%s", secid, attempt, exc)
            if attempt < self.retry_times:
                time.sleep(min(2, attempt))
        raise RuntimeError(f"EastMoney API Error: {last_error}")


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None: return default
    text = str(value).strip().replace(",", "")
    if not text: return default
    try:
        return float(text)
    except ValueError:
        return default


def infer_market(code: str) -> str:
    if code.startswith(("6", "9", "5")): return "sh"
    return "sz"


def normalize_code(code: str) -> str:
    digits = "".join(ch for ch in str(code).strip() if ch.isdigit())
    return digits.zfill(6) if digits else ""


def read_config(path: Path) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    if not path.exists(): return config
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line: continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value.startswith("[") and raw_value.endswith("]"):
            value = [int(item.strip()) for item in raw_value[1:-1].split(",") if item.strip()]
        elif raw_value.lower() in {"true", "false"}:
            value = raw_value.lower() == "true"
        else:
            try:
                value = int(raw_value)
            except ValueError:
                try:
                    value = float(raw_value)
                except ValueError:
                    value = raw_value.strip("'\"")
        config[key] = value
    return config


def read_stocks(path: Path) -> list[Stock]:
    if not path.exists(): raise FileNotFoundError(f"stock list not found: {path}")
    stocks: list[Stock] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = normalize_code(str(row.get("code") or ""))
            if not code: continue
            market = str(row.get("market") or "").strip().lower() or infer_market(code)
            stocks.append(Stock(code=code, name=str(row.get("name") or "").strip(), market=market))
    return stocks


def calculate_ma(bars: list[DailyBar], windows: list[int]) -> dict[int, float | None]:
    closes = [bar.close for bar in bars]
    ma: dict[int, float | None] = {}
    for window in windows:
        if len(closes) < window:
            ma[window] = None
        else:
            ma[window] = round(sum(closes[-window:]) / window, 3)
    return ma


def calculate_ma_series(bars: list[DailyBar], window: int) -> list[float | None]:
    closes = [bar.close for bar in bars]
    series: list[float | None] = []
    for idx in range(len(closes)):
        if idx + 1 < window:
            series.append(None)
            continue
        segment = closes[idx + 1 - window: idx + 1]
        series.append(sum(segment) / window)
    return series


def ma_position_status(close: float, ma_value: float | None, threshold_pct: float, window: int) -> tuple[
    str, float | None]:
    if ma_value is None or ma_value <= 0: return "N/A", None
    diff_pct = round((close - ma_value) / ma_value * 100, 2)
    if diff_pct > threshold_pct: return f"{window}日线上", diff_pct
    if diff_pct < -threshold_pct: return f"{window}日线下", diff_pct
    return f"贴近{window}日线", diff_pct


def get_base_overall_status(close: float, ma: dict[int, float | None]) -> str:
    required = [5, 10, 20, 30, 60]
    if any(ma.get(window) is None for window in required): return "数据不足"
    ma5, ma10, ma20, ma30, ma60 = [ma[window] for window in required]
    if close > ma5 > ma10 > ma20 > ma30 > ma60: return "强多头"
    if close < ma5 < ma10 < ma20 < ma30 < ma60: return "强空头"
    if close > ma20 and close > ma60: return "偏多"
    if close < ma20 and close < ma60: return "偏空"
    return "震荡"


def analyze_trend_retracement_and_break(bars: list[DailyBar], windows: list[int]) -> dict[str, Any]:
    ordered_windows = sorted(windows)
    ma_map = {window: calculate_ma_series(bars, window) for window in ordered_windows}
    trend_short_window = 20 if 20 in ma_map else ordered_windows[0]
    trend_long_window = 60 if 60 in ma_map else ordered_windows[-1]

    up_continue = {w: 0 for w in ordered_windows}
    up_break = {w: 0 for w in ordered_windows}
    weak_continue = {w: 0 for w in ordered_windows}
    weak_reverse = {w: 0 for w in ordered_windows}

    in_up_touch = {w: False for w in ordered_windows}
    in_weak_touch = {w: False for w in ordered_windows}
    current_mode = "none"

    for idx, bar in enumerate(bars):
        short_ma = ma_map[trend_short_window][idx]
        long_ma = ma_map[trend_long_window][idx]

        if short_ma is None or long_ma is None:
            mode = "none"
        elif bar.close > short_ma and short_ma > long_ma:
            mode = "up"
        elif bar.close < short_ma and short_ma < long_ma:
            mode = "weak"
        else:
            mode = "none"

        if mode != current_mode:
            if current_mode == "up":
                for w in ordered_windows:
                    if in_up_touch[w]: up_break[w] += 1; in_up_touch[w] = False
            elif current_mode == "weak":
                for w in ordered_windows:
                    if in_weak_touch[w]: weak_reverse[w] += 1; in_weak_touch[w] = False

            if mode != "up": in_up_touch = {w: False for w in ordered_windows}
            if mode != "weak": in_weak_touch = {w: False for w in ordered_windows}
            current_mode = mode

        if current_mode == "up":
            for w in ordered_windows:
                ma_value = ma_map[w][idx]
                if ma_value is None: continue
                if not in_up_touch[w] and bar.low <= ma_value: in_up_touch[w] = True
                if in_up_touch[w] and bar.close > ma_value: up_continue[w] += 1; in_up_touch[w] = False
        elif current_mode == "weak":
            for w in ordered_windows:
                ma_value = ma_map[w][idx]
                if ma_value is None: continue
                if not in_weak_touch[w] and bar.high >= ma_value: in_weak_touch[w] = True
                if in_weak_touch[w] and bar.close < ma_value: weak_continue[w] += 1; in_weak_touch[w] = False

    stats = {"up": {}, "weak": {}}
    trend_logs = []
    has_valid_data = False

    up_logs = []
    for w in ordered_windows:
        total = up_continue[w] + up_break[w]
        cont_pct = int(up_continue[w] / total * 100) if total > 0 else 0
        stats["up"][w] = {"total": total, "cont_pct": cont_pct, "break_pct": 100 - cont_pct if total > 0 else 0,
                          "cont_count": up_continue[w], "break_count": up_break[w]}
        if total > 0:
            up_logs.append(
                f"MA{w} 历史回踩{total}次: 继续趋势 {up_continue[w]}次({cont_pct}%) / 破位 {up_break[w]}次({stats['up'][w]['break_pct']}%)")

    if up_logs:
        trend_logs.append("【上升趋势复盘】")
        trend_logs.extend(up_logs)
        has_valid_data = True

    weak_logs = []
    for w in ordered_windows:
        total = weak_continue[w] + weak_reverse[w]
        cont_pct = int(weak_continue[w] / total * 100) if total > 0 else 0
        stats["weak"][w] = {"total": total, "cont_pct": cont_pct, "rev_pct": 100 - cont_pct if total > 0 else 0,
                            "cont_count": weak_continue[w], "rev_count": weak_reverse[w]}
        if total > 0:
            weak_logs.append(
                f"MA{w} 历史反抽{total}次: 继续下跌 {weak_continue[w]}次({cont_pct}%) / 反转 {weak_reverse[w]}次({stats['weak'][w]['rev_pct']}%)")

    if weak_logs:
        trend_logs.append("【下跌趋势复盘】")
        trend_logs.extend(weak_logs)
        has_valid_data = True

    return {
        "stats": stats,
        "summary": "包含回踩与反抽历史统计" if has_valid_data else "暂无回踩或反转历史数据",
        "logs": trend_logs if has_valid_data else ["历史数据未满足判定条件"]
    }


def analyze_drawdown_from_recent_peak(bars: list[DailyBar]) -> dict[str, Any]:
    if not bars: return {"summary": "无数据", "log": "无可用K线数据"}
    latest = bars[-1]
    recent_peak = latest
    for idx in range(len(bars) - 2, 0, -1):
        if bars[idx].close >= bars[idx - 1].close and bars[idx].close >= bars[idx + 1].close:
            recent_peak = bars[idx]
            break
    if recent_peak.close <= 0: return {"summary": "无有效高点", "log": "最近极值高点无效"}
    diff_pct = round((latest.close - recent_peak.close) / recent_peak.close * 100, 2)
    down_pct = round(abs(diff_pct), 2) if diff_pct < 0 else 0.0
    return {
        "summary": f"较极值高点({recent_peak.date} {recent_peak.close:.2f})下跌 {down_pct:.2f}%",
        "log": f"当前价 {latest.close:.2f}；相较 {recent_peak.date} 高点 {recent_peak.close:.2f}，变化 {diff_pct:.2f}%",
    }


def analyze_stock(
        stock: Stock, primary_source: StockDataSource, secondary_source: StockDataSource,
        windows: list[int], threshold_pct: float, global_latest_date: str | None, history_limit: Any,
) -> dict[str, Any]:
    if stock.market not in {"sh", "sz"} or not re.fullmatch(r"\d{6}", stock.code):
        return failed_result(stock, "股票代码无效")

    limit = 5000 if str(history_limit).lower() == "all" else max(int(history_limit), max(windows) + 20)
    remarks: list[str] = []
    bars = []

    try:
        bars = primary_source.get_daily_bars(stock.code, stock.market, limit)
    except Exception as e:
        logging.warning("Primary source failed for %s: %s", stock.code, e)

    # 无缝切换到高可靠备用源
    if not bars:
        try:
            bars = secondary_source.get_daily_bars(stock.code, stock.market, limit)
            if bars:
                remarks.append(f"主源失败，已无缝切换至备用源({secondary_source.name})")
        except Exception as e:
            logging.warning("Secondary source also failed for %s: %s", stock.code, e)

    if not bars: return failed_result(stock, "所有数据源均拉取失败")

    latest = bars[-1]
    ma = calculate_ma(bars, windows)
    ma_status, diff_pct = {}, {}
    for window in windows:
        status, diff = ma_position_status(latest.close, ma.get(window), threshold_pct, window)
        ma_status[window] = status
        diff_pct[window] = diff

    base_status = get_base_overall_status(latest.close, ma)
    trend_analysis = analyze_trend_retracement_and_break(bars, windows)

    # 结合历史复盘生成推演结论面板与按钮
    prob_suffix = ""
    valid_diffs = {w: abs(diff) for w, diff in diff_pct.items() if diff is not None}
    if valid_diffs and base_status not in ["震荡", "数据不足"]:
        nearest_w = min(valid_diffs, key=valid_diffs.get)
        stats = trend_analysis.get("stats", {})

        if base_status in ["强多头", "偏多"]:
            w_stats = stats.get("up", {}).get(nearest_w, {})
            if w_stats.get("total", 0) > 0:
                cont_pct, cont_count, break_count = w_stats["cont_pct"], w_stats["cont_count"], w_stats["break_count"]
                prob = "向上" if cont_pct >= 50 else "向下"
                icon = "📈" if prob == "向上" else "📉"
                detail = (
                    f"【推演依据】\n"
                    f"当前状态：{base_status}\n"
                    f"最近支撑线：MA{nearest_w}\n\n"
                    f"【历史数据复盘】\n"
                    f"历史同趋势下回踩该均线共 {w_stats['total']} 次：\n"
                    f"▶ 顺势企稳：{cont_pct}% ({cont_count}次)\n"
                    f"▶ 逆势破位：{w_stats['break_pct']}% ({break_count}次)\n\n"
                    f"【系统结论】\n"
                    f"{'由于顺势企稳概率较高' if prob == '向上' else '由于逆势破位发生较多'}，推演大概率 {prob}。"
                )
                prob_suffix = f" <span class='deduction-badge' onclick='showDeduction(this)' data-detail='{escape(detail)}'>{icon} 推演{prob}</span>"

        elif base_status in ["强空头", "偏空"]:
            w_stats = stats.get("weak", {}).get(nearest_w, {})
            if w_stats.get("total", 0) > 0:
                rev_pct, cont_pct, cont_count, rev_count = w_stats["rev_pct"], w_stats["cont_pct"], w_stats[
                    "cont_count"], w_stats["rev_count"]
                prob = "向上" if rev_pct >= 50 else "向下"
                icon = "📈" if prob == "向上" else "📉"
                detail = (
                    f"【推演依据】\n"
                    f"当前状态：{base_status}\n"
                    f"最近阻力线：MA{nearest_w}\n\n"
                    f"【历史数据复盘】\n"
                    f"历史同趋势下反抽该均线共 {w_stats['total']} 次：\n"
                    f"▶ 顺势受阻：{cont_pct}% ({cont_count}次)\n"
                    f"▶ 逆势突破：{rev_pct}% ({rev_count}次)\n\n"
                    f"【系统结论】\n"
                    f"{'由于逆势反转突破概率较高' if prob == '向上' else '由于顺势受阻下跌概率为主'}，推演大概率 {prob}。"
                )
                prob_suffix = f" <span class='deduction-badge' onclick='showDeduction(this)' data-detail='{escape(detail)}'>{icon} 推演{prob}</span>"

    if len(bars) < max(windows): remarks.append(f"有效交易日不足 {max(windows)} 日")
    if global_latest_date and latest.date < global_latest_date: remarks.append("疑似停牌或未更新")

    return {
        "code": stock.code, "name": stock.name, "market": stock.market,
        "latest_trade_date": latest.date, "close": latest.close,
        "ma": ma, "ma_status": ma_status, "diff_pct": diff_pct,
        "base_status": base_status,
        "overall_status": base_status + prob_suffix,
        "trend_analysis": trend_analysis,
        "drawdown_analysis": analyze_drawdown_from_recent_peak(bars),
        "remark": "；".join(remarks), "success": True,
    }


def failed_result(stock: Stock, remark: str) -> dict[str, Any]:
    return {
        "code": stock.code, "name": stock.name, "market": stock.market,
        "latest_trade_date": "", "close": None, "ma": {}, "ma_status": {}, "diff_pct": {},
        "base_status": "数据不足", "overall_status": "数据不足",
        "trend_analysis": {"summary": "无分析结果", "logs": [remark]},
        "drawdown_analysis": {"summary": "无分析结果", "log": remark},
        "remark": remark, "success": False,
    }


def render_html(results: list[dict[str, Any]], config: dict[str, Any], output_path: Path) -> None:
    windows = [int(item) for item in config["ma_windows"]]
    latest_dates = [item["latest_trade_date"] for item in results if item.get("latest_trade_date")]
    latest_trade_date = max(latest_dates) if latest_dates else "N/A"

    status_counts = {"强多头": 0, "偏多": 0, "震荡": 0, "偏空": 0, "强空头": 0, "数据不足": 0}
    for item in results:
        s = item.get("base_status", "数据不足")
        status_counts[s] = status_counts.get(s, 0) + 1

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = "\n".join(render_row(item, windows) for item in results)
    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A股均线监控报告 (推演弹窗版)</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2937; background: #f5f7fb; }}
    header {{ padding: 24px 28px; background: #ffffff; border-bottom: 1px solid #e5e7eb; }}
    h1 {{ margin: 0 0 12px; font-size: 24px; display: flex; align-items: center; gap: 8px; }}
    .badge {{ font-size: 12px; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-weight: 500; border: 1px solid #bbf7d0; }}
    .status-summary {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }}
    .status-card {{ display: flex; flex-direction: column; padding: 12px 16px; border-radius: 8px; cursor: pointer; transition: transform 0.1s, box-shadow 0.1s; border: 1px solid #e5e7eb; background: #fff; min-width: 90px; text-align: center; }}
    .status-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
    .status-card span.count {{ font-size: 20px; font-weight: 700; margin-top: 4px; }}
    .status-card.total {{ background: #f3f4f6; color: #374151; }}
    .status-card.strong-bull {{ background: #fef2f2; color: #991b1b; border-color: #fecaca; }}
    .status-card.bull {{ background: #fff1f2; color: #be123c; border-color: #ffe4e6; }}
    .status-card.neutral {{ background: #fdf4ff; color: #86198f; border-color: #fae8ff; }}
    .status-card.bear {{ background: #ecfdf5; color: #047857; border-color: #d1fae5; }}
    .status-card.strong-bear {{ background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }}
    .status-card.insufficient {{ background: #f9fafb; color: #6b7280; }}

    main {{ padding: 20px 28px 32px; }}
    .toolbar {{ display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }}
    input, select {{ height: 36px; padding: 0 10px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; }}
    .table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1460px; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid #e5e7eb; text-align: right; white-space: nowrap; }}
    th {{ position: sticky; top: 0; background: #f9fafb; cursor: grab; font-size: 13px; user-select: none; z-index: 10; }}
    th:active {{ cursor: grabbing; }}
    th.dragging {{ opacity: 0.5; background: #e5e7eb; }}
    td:first-child, td:nth-child(2), th:first-child, th:nth-child(2) {{ text-align: left; z-index: 11; }}
    tr.error {{ background: #fff7ed; }}

    .up, .bull, .strong-bull {{ color: #b91c1c; font-weight: 600; }}
    .down, .bear, .strong-bear {{ color: #047857; font-weight: 600; }}
    .near {{ color: #b45309; font-weight: 600; }}
    .neutral {{ color: #4b5563; font-weight: 600; }}
    .insufficient {{ color: #374151; font-weight: 600; }}

    /* 弹窗与徽章样式 */
    .deduction-badge {{ background: #fffbeb; color: #d97706; padding: 3px 8px; border-radius: 6px; border: 1px solid #fde68a; cursor: pointer; font-size: 12px; margin-left: 6px; transition: all 0.2s; font-weight: normal; }}
    .deduction-badge:hover {{ background: #fef3c7; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}

    .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.4); backdrop-filter: blur(2px); }}
    .modal-content {{ background-color: #fff; margin: 8% auto; padding: 24px; border: 1px solid #e5e7eb; width: 90%; max-width: 380px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); line-height: 1.6; position: relative; font-size: 14px; color: #374151; }}
    .close-btn {{ color: #9ca3af; position: absolute; right: 20px; top: 16px; font-size: 24px; font-weight: bold; cursor: pointer; transition: color 0.2s; }}
    .close-btn:hover {{ color: #1f2937; }}

    details {{ max-width: 450px; text-align: left; }}
    details summary {{ cursor: pointer; color: #374151; }}
    .log-list {{ margin: 8px 0 0; padding-left: 16px; font-size: 13px; }}
    .log-list li {{ margin-bottom: 4px; }}
    .warn-text {{ color: #b45309; font-size: 12px; font-weight: bold; }}
  </style>
</head>
<body>
  <header>
    <h1>A股均线监控报告 <span class="badge">概率推演引擎 & 容灾数据双驱</span></h1>
    <div style="color: #6b7280; font-size: 13px;">生成时间: {escape(generated_at)} | 最近交易日: {escape(latest_trade_date)} | 主源:腾讯(前复权) / 备用:东方财富(前复权)</div>
    <div class="status-summary">
      <div class="status-card total" onclick="filterStatus('')">全部<span class="count">{len(results)}</span></div>
      <div class="status-card strong-bull" onclick="filterStatus('强多头')">强多头<span class="count">{status_counts['强多头']}</span></div>
      <div class="status-card bull" onclick="filterStatus('偏多')">偏多<span class="count">{status_counts['偏多']}</span></div>
      <div class="status-card neutral" onclick="filterStatus('震荡')">震荡<span class="count">{status_counts['震荡']}</span></div>
      <div class="status-card bear" onclick="filterStatus('偏空')">偏空<span class="count">{status_counts['偏空']}</span></div>
      <div class="status-card strong-bear" onclick="filterStatus('强空头')">强空头<span class="count">{status_counts['强空头']}</span></div>
      <div class="status-card insufficient" onclick="filterStatus('数据不足')">缺数据<span class="count">{status_counts['数据不足']}</span></div>
    </div>
  </header>
  <main>
    <div class="toolbar">
      <input id="searchInput" placeholder="搜索代码或名称" style="width: 200px;">
      <select id="statusFilter" style="display: none;">
        <option value="">全部状态</option>
        <option>强多头</option><option>偏多</option><option>震荡</option>
        <option>偏空</option><option>强空头</option><option>数据不足</option>
      </select>
      <span style="font-size: 12px; color: #6b7280; margin-left: 10px;">💡 提示：点击黄色【推演按钮】可查看决策链路；拖拽表头可移动位置。</span>
    </div>
    <div class="table-wrap">
      <table id="reportTable">
        <thead>{render_header(windows)}</thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div id="deductionModal" class="modal">
      <div class="modal-content">
        <span class="close-btn" onclick="closeDeduction()">&times;</span>
        <h3 style="margin-top:0; color:#111827; border-bottom:1px solid #e5e7eb; padding-bottom:12px; font-size: 18px;">💡 AI 推演过程明细</h3>
        <div id="deductionText"></div>
      </div>
    </div>

  </main>
  <script>
    // --- 筛选与排序交互 ---
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const table = document.getElementById('reportTable');

    function applyFilter() {{
      const keyword = searchInput.value.trim().toLowerCase();
      const status = statusFilter.value;
      for (const row of table.tBodies[0].rows) {{
        const text = row.innerText.toLowerCase();
        const matchedKeyword = !keyword || text.includes(keyword);
        const matchedStatus = !status || row.dataset.status === status;
        row.style.display = matchedKeyword && matchedStatus ? '' : 'none';
      }}
    }}
    function filterStatus(status) {{ statusFilter.value = status; applyFilter(); }}
    searchInput.addEventListener('input', applyFilter);

    // --- 推演弹窗逻辑 ---
    function showDeduction(element) {{
        event.stopPropagation(); // 阻止表格冒泡排序
        const rawText = element.getAttribute('data-detail');
        // 将普通换行替换为 html 换行，并高亮小标题
        let formatted = rawText.replace(/\\n/g, '<br>');
        formatted = formatted.replace(/【推演依据】|【历史数据复盘】|【系统结论】/g, match => 
            `<span style="color:#2563eb; font-weight:bold; font-size:15px; display:inline-block; margin-top:12px; margin-bottom:4px;">${{match}}</span>`
        );
        document.getElementById('deductionText').innerHTML = formatted;
        document.getElementById('deductionModal').style.display = 'block';
    }}
    function closeDeduction() {{ document.getElementById('deductionModal').style.display = 'none'; }}
    window.onclick = function(event) {{
        const modal = document.getElementById('deductionModal');
        if (event.target === modal) {{ modal.style.display = 'none'; }}
    }}

    // --- 表格拖拽 ---
    const headers = table.querySelectorAll('th');
    headers.forEach((th) => {{
      th.addEventListener('click', function(e) {{
        if (this.classList.contains('dragging')) return; 
        const index = Array.from(this.parentNode.children).indexOf(this);
        const rows = Array.from(table.tBodies[0].rows);
        const asc = this.dataset.asc !== 'true';
        rows.sort((a, b) => {{
          const av = a.cells[index].dataset.value || a.cells[index].innerText;
          const bv = b.cells[index].dataset.value || b.cells[index].innerText;
          const an = Number(av), bn = Number(bv);
          const result = Number.isFinite(an) && Number.isFinite(bn) ? an - bn : av.localeCompare(bv, 'zh-CN');
          return asc ? result : -result;
        }});
        this.dataset.asc = String(asc);
        rows.forEach(row => table.tBodies[0].appendChild(row));
      }});
    }});

    let draggedIndex = null;
    headers.forEach(th => {{
      th.draggable = true;
      th.addEventListener('dragstart', function(e) {{
        draggedIndex = Array.from(this.parentNode.children).indexOf(this);
        e.dataTransfer.effectAllowed = 'move';
        setTimeout(() => this.classList.add('dragging'), 0);
      }});
      th.addEventListener('dragend', function() {{ this.classList.remove('dragging'); draggedIndex = null; }});
      th.addEventListener('dragover', function(e) {{ e.preventDefault(); }});
      th.addEventListener('drop', function(e) {{
        e.preventDefault();
        const targetTh = this.closest('th');
        if (!targetTh) return;
        const targetIndex = Array.from(targetTh.parentNode.children).indexOf(targetTh);
        if (draggedIndex === null || draggedIndex === targetIndex) return;

        const rowsToMove = [table.tHead.rows[0], ...Array.from(table.tBodies[0].rows)];
        rowsToMove.forEach(row => {{
          const cells = Array.from(row.children);
          const draggedCell = cells[draggedIndex];
          const targetCell = cells[targetIndex];
          if(draggedIndex < targetIndex) {{ targetCell.parentNode.insertBefore(draggedCell, targetCell.nextSibling); }} 
          else {{ targetCell.parentNode.insertBefore(draggedCell, targetCell); }}
        }});
        draggedIndex = targetIndex; 
      }});
    }});
  </script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")


def render_header(windows: list[int]) -> str:
    items = ["代码", "名称", "综合状态(含概率推演)", "收盘价"]
    for window in windows: items.extend([f"MA{window}", f"MA{window}状态"])
    items.extend(["趋势分析复盘", "极值回撤", "最近交易日", "系统备注"])
    return "<tr>" + "".join(f"<th>{escape(item)}</th>" for item in items) + "</tr>"


def render_row(item: dict[str, Any], windows: list[int]) -> str:
    cells = [
        td(item["code"]), td(item["name"] or "--"),
        td_raw(item["overall_status"], css_class=status_class(item["base_status"])),
        td_number(item["close"]),
    ]
    for window in windows:
        cells.append(td_number(item["ma"].get(window)))
        status = item["ma_status"].get(window, "N/A")
        cells.append(td(status, css_class=status_class(status)))

    trend = item.get("trend_analysis", {})
    trend_logs = trend.get("logs", [])
    trend_html = [f"<div>{escape(trend.get('summary', ''))}</div>"]
    if len(trend_logs) > 1:
        log_items = "".join(f"<li>{escape(text)}</li>" for text in trend_logs)
        trend_html.append(
            f"<details><summary>展开详细统计</summary><ul class=\"log-list\" style=\"list-style:none; padding-left:0;\">{log_items}</ul></details>")
    elif trend_logs:
        trend_html.append(f"<div style='font-size:12px; color:#6b7280;'>{escape(trend_logs[0])}</div>")
    cells.append(td_raw("".join(trend_html)))

    drawdown = item.get("drawdown_analysis", {})
    drawdown_html = [f"<div>{escape(drawdown.get('summary', ''))}</div>"]
    if drawdown.get("log"): drawdown_html.append(
        f"<details><summary>展开日志</summary><div>{escape(drawdown.get('log'))}</div></details>")
    cells.append(td_raw("".join(drawdown_html)))

    cells.append(td(item["latest_trade_date"] or "--"))

    remark = item["remark"] or ""
    css_class = "warn-text" if "切换至备用源" in remark else ""
    cells.append(td(remark, css_class))

    row_class = " class=\"error\"" if not item["success"] else ""
    return f"<tr{row_class} data-status=\"{escape(item['base_status'])}\">" + "".join(cells) + "</tr>"


def td(value: Any, css_class: str = "") -> str:
    return f"<td class=\"{css_class}\">{escape(value)}</td>" if css_class else f"<td>{escape(value)}</td>"


def td_raw(html_value: str, css_class: str = "") -> str:
    return f"<td class=\"{css_class}\">{html_value}</td>" if css_class else f"<td>{html_value}</td>"


def td_number(value: Any) -> str:
    if value is None: return "<td data-value=\"\">N/A</td>"
    number = float(value)
    return f"<td data-value=\"{number:.4f}\">{number:.2f}</td>"


def escape(value: Any) -> str: return html.escape(str(value), quote=True)


def status_class(status: str) -> str:
    if "强多头" in status: return "strong-bull"
    if "偏多" in status or "线上" in status: return "bull"
    if "强空头" in status: return "strong-bear"
    if "偏空" in status or "线下" in status: return "bear"
    if "贴近" in status: return "near"
    if status == "数据不足" or status == "N/A" or status == "震荡": return "insufficient"
    return "neutral"


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(log_dir / "monitor.log", encoding="utf-8"),
                                  logging.StreamHandler(sys.stdout)])


def run(config_path: Path, stocks_path: Path) -> Path:
    setup_logging()
    config = read_config(config_path)
    stocks = read_stocks(stocks_path)
    if not stocks: raise ValueError(f"no stocks found in {stocks_path}")

    timeout = int(config.get("request_timeout_seconds", 10))
    retries = int(config.get("retry_times", 3))

    primary_source = TencentDataSource(timeout, retries)
    secondary_source = EastMoneyDataSource(timeout, retries)

    windows = [int(item) for item in config["ma_windows"]]
    threshold_pct = float(config["near_threshold_pct"])
    history_limit = config.get("history_limit", "all")

    results: list[dict[str, Any]] = []
    latest_seen: str | None = None
    for stock in stocks:
        try:
            result = analyze_stock(stock, primary_source, secondary_source, windows, threshold_pct, latest_seen,
                                   history_limit)
            if result.get("latest_trade_date"):
                latest_seen = max(latest_seen or result["latest_trade_date"], result["latest_trade_date"])
        except Exception as exc:
            logging.exception("stock failed: code=%s market=%s", stock.code, stock.market)
            result = failed_result(stock, f"系统异常：{exc}")
        results.append(result)

    global_latest = max((item["latest_trade_date"] for item in results if item.get("latest_trade_date")), default=None)
    if global_latest:
        for item in results:
            if item["success"] and item["latest_trade_date"] < global_latest and "疑似停牌或未更新" not in item[
                "remark"]:
                item["remark"] = "；".join(part for part in [item["remark"], "疑似停牌或未更新"] if part)

    output_path = Path(str(config["output_path"]))
    render_html(results, config, output_path)
    logging.info("report generated: %s success=%s failed=%s", output_path,
                 sum(1 for item in results if item["success"]), sum(1 for item in results if not item["success"]))
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="A stock moving average monitor")
    parser.add_argument("--config", default="config.yaml", help="config file path")
    parser.add_argument("--stocks", default="stocks.csv", help="stock list csv path")
    args = parser.parse_args()
    output_path = run(Path(args.config), Path(args.stocks))
    print(f"HTML report generated: {output_path}")


if __name__ == "__main__":
    main()