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
    "data_source": "sina",
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


class SinaDataSource(StockDataSource):
    name = "新浪财经"

    def __init__(self, timeout_seconds: int = 10, retry_times: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.retry_times = retry_times

    def get_daily_bars(self, code: str, market: str, limit: int = 80) -> list[DailyBar]:
        symbol = f"{market}{code}"
        urls = [
            "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            f"CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={limit}",
            "https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20data=/"
            f"CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={limit}",
        ]
        last_error: Exception | None = None
        for attempt in range(1, self.retry_times + 1):
            for url in urls:
                try:
                    payload = self._fetch(url)
                    return self._parse_payload(payload)
                except Exception as exc:
                    last_error = exc
                    logging.warning("fetch failed: symbol=%s attempt=%s url=%s error=%s", symbol, attempt, url, exc)
            if attempt < self.retry_times:
                time.sleep(min(2, attempt))
        raise RuntimeError(str(last_error or "unknown sina api error"))

    def _fetch(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _parse_payload(self, payload: str) -> list[DailyBar]:
        text = payload.strip()
        if not text:
            return []
        match = re.search(r"(\[.*\])", text, re.S)
        if match:
            text = match.group(1)
        data = json.loads(text)
        if not isinstance(data, list):
            return []
        bars: list[DailyBar] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            day = str(item.get("day") or item.get("date") or "").strip()
            close = to_float(item.get("close"))
            if not day or close <= 0:
                continue
            bars.append(
                DailyBar(
                    date=day[:10],
                    open=to_float(item.get("open")),
                    high=to_float(item.get("high")),
                    low=to_float(item.get("low")),
                    close=close,
                    volume=to_float(item.get("volume")),
                )
            )
        bars.sort(key=lambda bar: bar.date)
        return bars


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip().replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def infer_market(code: str) -> str:
    if code.startswith(("6", "9")):
        return "sh"
    return "sz"


def normalize_code(code: str) -> str:
    digits = "".join(ch for ch in str(code).strip() if ch.isdigit())
    return digits.zfill(6) if digits else ""


def read_config(path: Path) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    if not path.exists():
        return config
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
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
    if not path.exists():
        raise FileNotFoundError(f"stock list not found: {path}")
    stocks: list[Stock] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = normalize_code(str(row.get("code") or ""))
            if not code:
                continue
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


def ma_position_status(close: float, ma_value: float | None, threshold_pct: float, window: int) -> tuple[str, float | None]:
    if ma_value is None or ma_value <= 0:
        return "N/A", None
    diff_pct = round((close - ma_value) / ma_value * 100, 2)
    if diff_pct > threshold_pct:
        return f"{window}日线上", diff_pct
    if diff_pct < -threshold_pct:
        return f"{window}日线下", diff_pct
    return f"贴近{window}日线", diff_pct


def overall_status(close: float, ma: dict[int, float | None]) -> str:
    required = [5, 10, 20, 30, 60]
    if any(ma.get(window) is None for window in required):
        return "数据不足"
    ma5, ma10, ma20, ma30, ma60 = [ma[window] for window in required]
    assert all(value is not None for value in (ma5, ma10, ma20, ma30, ma60))
    if close > ma5 > ma10 > ma20 > ma30 > ma60:
        return "强多头"
    if close < ma5 < ma10 < ma20 < ma30 < ma60:
        return "强空头"
    if close > ma20 and close > ma60:
        return "偏多"
    if close < ma20 and close < ma60:
        return "偏空"
    return "震荡"


def analyze_trend_retracement_and_break(
    bars: list[DailyBar],
    windows: list[int],
) -> dict[str, Any]:
    ordered_windows = sorted(windows)
    ma_map = {window: calculate_ma_series(bars, window) for window in ordered_windows}
    trend_short_window = 20 if 20 in ma_map else ordered_windows[0]
    trend_long_window = 60 if 60 in ma_map else ordered_windows[-1]
    trend_logs: list[str] = []
    up_touch_count = {window: 0 for window in ordered_windows}
    weak_break_count = {window: 0 for window in ordered_windows}

    current_mode = "none"
    seg_start = ""
    seg_end = ""
    seg_deepest_up: int | None = None
    seg_deepest_weak: int | None = None

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
            if current_mode == "up" and seg_start and seg_end:
                if seg_deepest_up is None:
                    trend_logs.append(f"上升趋势 {seg_start}~{seg_end} 未触及均线")
                else:
                    trend_logs.append(f"上升趋势 {seg_start}~{seg_end} 最多回踩 MA{seg_deepest_up}")
            if current_mode == "weak" and seg_start and seg_end:
                if seg_deepest_weak is None:
                    trend_logs.append(f"走弱趋势 {seg_start}~{seg_end} 未跌破均线")
                else:
                    trend_logs.append(f"走弱趋势 {seg_start}~{seg_end} 一般跌破 MA{seg_deepest_weak}")
            current_mode = mode
            seg_start = bar.date if mode in {"up", "weak"} else ""
            seg_deepest_up = None
            seg_deepest_weak = None

        if mode not in {"up", "weak"}:
            seg_end = ""
            continue

        seg_end = bar.date
        if mode == "up":
            touched_today: int | None = None
            for window in ordered_windows:
                ma_value = ma_map[window][idx]
                if ma_value is not None and bar.low <= ma_value:
                    up_touch_count[window] += 1
                    touched_today = window
            if touched_today is not None:
                trend_logs.append(f"{bar.date} 上升趋势回踩 MA{touched_today}")
                seg_deepest_up = max(seg_deepest_up or touched_today, touched_today)
        else:
            broken_today: int | None = None
            for window in ordered_windows:
                ma_value = ma_map[window][idx]
                if ma_value is not None and bar.close < ma_value:
                    weak_break_count[window] += 1
                    broken_today = window
            if broken_today is not None:
                trend_logs.append(f"{bar.date} 走弱趋势跌破 MA{broken_today}")
                seg_deepest_weak = max(seg_deepest_weak or broken_today, broken_today)

    if current_mode == "up" and seg_start and seg_end:
        if seg_deepest_up is None:
            trend_logs.append(f"上升趋势 {seg_start}~{seg_end} 未触及均线")
        else:
            trend_logs.append(f"上升趋势 {seg_start}~{seg_end} 最多回踩 MA{seg_deepest_up}")
    if current_mode == "weak" and seg_start and seg_end:
        if seg_deepest_weak is None:
            trend_logs.append(f"走弱趋势 {seg_start}~{seg_end} 未跌破均线")
        else:
            trend_logs.append(f"走弱趋势 {seg_start}~{seg_end} 一般跌破 MA{seg_deepest_weak}")

    up_summary = "，".join([f"MA{window}:{up_touch_count[window]}次" for window in ordered_windows])
    weak_summary = "，".join([f"MA{window}:{weak_break_count[window]}次" for window in ordered_windows])
    if not trend_logs:
        trend_logs.append("未识别到有效上升/走弱趋势区间")
    return {
        "up_touch_count": up_touch_count,
        "weak_break_count": weak_break_count,
        "summary": f"上升趋势回踩统计({up_summary})；走弱趋势跌破统计({weak_summary})",
        "logs": trend_logs,
    }


def analyze_drawdown_from_recent_peak(bars: list[DailyBar]) -> dict[str, Any]:
    if not bars:
        return {"summary": "无数据", "log": "无可用K线数据"}
    latest = bars[-1]
    recent_peak = latest
    for idx in range(len(bars) - 2, 0, -1):
        prev_close = bars[idx - 1].close
        curr_close = bars[idx].close
        next_close = bars[idx + 1].close
        if curr_close >= prev_close and curr_close >= next_close:
            recent_peak = bars[idx]
            break
    if recent_peak.close <= 0:
        return {"summary": "无有效高点", "log": "最近极值高点无效"}
    diff_pct = round((latest.close - recent_peak.close) / recent_peak.close * 100, 2)
    down_pct = round(abs(diff_pct), 2) if diff_pct < 0 else 0.0
    summary = f"较最近极值高点({recent_peak.date} {recent_peak.close:.2f})下跌 {down_pct:.2f}%"
    log = f"当前价 {latest.close:.2f}；相较 {recent_peak.date} 高点 {recent_peak.close:.2f}，变化 {diff_pct:.2f}%"
    return {
        "peak_date": recent_peak.date,
        "peak_close": round(recent_peak.close, 2),
        "current_close": round(latest.close, 2),
        "diff_pct": diff_pct,
        "down_pct": down_pct,
        "summary": summary,
        "log": log,
    }


def analyze_stock(
    stock: Stock,
    source: StockDataSource,
    windows: list[int],
    threshold_pct: float,
    global_latest_date: str | None,
    history_limit: Any,
) -> dict[str, Any]:
    if stock.market not in {"sh", "sz"} or not re.fullmatch(r"\d{6}", stock.code):
        return failed_result(stock, "股票代码无效或无行情数据")
    if str(history_limit).lower() == "all":
        limit = 5000
    else:
        try:
            limit = max(int(history_limit), max(max(windows) + 20, 80))
        except (TypeError, ValueError):
            limit = 5000
    bars = source.get_daily_bars(stock.code, stock.market, limit)
    if not bars:
        return failed_result(stock, "股票代码无效或无行情数据")
    latest = bars[-1]
    ma = calculate_ma(bars, windows)
    ma_status: dict[int, str] = {}
    diff_pct: dict[int, float | None] = {}
    for window in windows:
        status, diff = ma_position_status(latest.close, ma.get(window), threshold_pct, window)
        ma_status[window] = status
        diff_pct[window] = diff
    trend_analysis = analyze_trend_retracement_and_break(bars, windows)
    drawdown_analysis = analyze_drawdown_from_recent_peak(bars)
    remarks: list[str] = []
    if len(bars) < max(windows):
        remarks.append(f"有效交易日不足 {max(windows)} 日")
    if global_latest_date and latest.date < global_latest_date:
        remarks.append("疑似停牌或未更新")
    return {
        "code": stock.code,
        "name": stock.name,
        "market": stock.market,
        "latest_trade_date": latest.date,
        "close": latest.close,
        "ma": ma,
        "ma_status": ma_status,
        "diff_pct": diff_pct,
        "overall_status": overall_status(latest.close, ma),
        "trend_analysis": trend_analysis,
        "drawdown_analysis": drawdown_analysis,
        "remark": "；".join(remarks),
        "success": True,
    }


def failed_result(stock: Stock, remark: str) -> dict[str, Any]:
    return {
        "code": stock.code,
        "name": stock.name,
        "market": stock.market,
        "latest_trade_date": "",
        "close": None,
        "ma": {},
        "ma_status": {},
        "diff_pct": {},
        "overall_status": "数据不足",
        "trend_analysis": {"summary": "无分析结果", "logs": [remark]},
        "drawdown_analysis": {"summary": "无分析结果", "log": remark},
        "remark": remark,
        "success": False,
    }


def render_html(results: list[dict[str, Any]], config: dict[str, Any], output_path: Path, source_name: str) -> None:
    windows = [int(item) for item in config["ma_windows"]]
    latest_dates = [item["latest_trade_date"] for item in results if item.get("latest_trade_date")]
    latest_trade_date = max(latest_dates) if latest_dates else "N/A"
    success_count = sum(1 for item in results if item["success"])
    failed_count = len(results) - success_count
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = "\n".join(render_row(item, windows) for item in results)
    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A股均线监控报告</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2937; background: #f5f7fb; }}
    header {{ padding: 24px 28px; background: #ffffff; border-bottom: 1px solid #e5e7eb; }}
    h1 {{ margin: 0 0 12px; font-size: 24px; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }}
    .metric {{ padding: 12px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }}
    .metric span {{ display: block; color: #6b7280; font-size: 12px; }}
    .metric strong {{ font-size: 18px; }}
    main {{ padding: 20px 28px 32px; }}
    .toolbar {{ display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }}
    input, select {{ height: 36px; padding: 0 10px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; }}
    .table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1460px; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid #e5e7eb; text-align: right; white-space: nowrap; }}
    th {{ position: sticky; top: 0; background: #f9fafb; cursor: pointer; font-size: 13px; }}
    td:first-child, td:nth-child(2), th:first-child, th:nth-child(2) {{ text-align: left; }}
    tr.error {{ background: #fff7ed; }}
    .up, .bull, .strong-bull {{ color: #b91c1c; font-weight: 600; }}
    .down, .bear, .strong-bear {{ color: #047857; font-weight: 600; }}
    .near {{ color: #b45309; font-weight: 600; }}
    .neutral {{ color: #4b5563; font-weight: 600; }}
    .insufficient {{ color: #374151; font-weight: 600; }}
    details {{ max-width: 360px; }}
    details summary {{ cursor: pointer; color: #374151; }}
    .log-list {{ margin: 8px 0 0; padding-left: 16px; }}
    .log-list li {{ margin-bottom: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>A股均线监控报告</h1>
    <div class="summary">
      <div class="metric"><span>报告生成时间</span><strong>{escape(generated_at)}</strong></div>
      <div class="metric"><span>最近交易日</span><strong>{escape(latest_trade_date)}</strong></div>
      <div class="metric"><span>股票数量</span><strong>{len(results)}</strong></div>
      <div class="metric"><span>成功数量</span><strong>{success_count}</strong></div>
      <div class="metric"><span>失败数量</span><strong>{failed_count}</strong></div>
      <div class="metric"><span>数据源</span><strong>{escape(source_name)}</strong></div>
    </div>
  </header>
  <main>
    <div class="toolbar">
      <input id="searchInput" placeholder="搜索股票代码或名称">
      <select id="statusFilter">
        <option value="">全部状态</option>
        <option>强多头</option><option>偏多</option><option>震荡</option>
        <option>偏空</option><option>强空头</option><option>数据不足</option>
      </select>
    </div>
    <div class="table-wrap">
      <table id="reportTable">
        <thead>{render_header(windows)}</thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </main>
  <script>
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
    searchInput.addEventListener('input', applyFilter);
    statusFilter.addEventListener('change', applyFilter);
    for (const th of table.tHead.rows[0].cells) {{
      th.addEventListener('click', () => {{
        const index = th.cellIndex;
        const rows = Array.from(table.tBodies[0].rows);
        const asc = th.dataset.asc !== 'true';
        rows.sort((a, b) => {{
          const av = a.cells[index].dataset.value || a.cells[index].innerText;
          const bv = b.cells[index].dataset.value || b.cells[index].innerText;
          const an = Number(av), bn = Number(bv);
          const result = Number.isFinite(an) && Number.isFinite(bn) ? an - bn : av.localeCompare(bv, 'zh-CN');
          return asc ? result : -result;
        }});
        th.dataset.asc = String(asc);
        rows.forEach(row => table.tBodies[0].appendChild(row));
      }});
    }}
  </script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")


def render_header(windows: list[int]) -> str:
    items = ["股票代码", "股票名称", "最近交易日", "收盘价"]
    for window in windows:
        items.extend([f"MA{window}", f"MA{window} 状态"])
    items.extend(["综合状态", "趋势分析", "极值回撤", "备注"])
    return "<tr>" + "".join(f"<th>{escape(item)}</th>" for item in items) + "</tr>"


def render_row(item: dict[str, Any], windows: list[int]) -> str:
    cells = [
        td(item["code"]),
        td(item["name"] or "--"),
        td(item["latest_trade_date"] or "--"),
        td_number(item["close"]),
    ]
    for window in windows:
        cells.append(td_number(item["ma"].get(window)))
        status = item["ma_status"].get(window, "N/A")
        cells.append(td(status, css_class=status_class(status)))
    cells.append(td(item["overall_status"], css_class=status_class(item["overall_status"])))
    trend = item.get("trend_analysis", {})
    trend_logs = trend.get("logs", [])
    trend_html = [f"<div>{escape(trend.get('summary', ''))}</div>"]
    if trend_logs:
        log_items = "".join(f"<li>{escape(text)}</li>" for text in trend_logs)
        trend_html.append(f"<details><summary>展开日志</summary><ul class=\"log-list\">{log_items}</ul></details>")
    cells.append(td_raw("".join(trend_html)))

    drawdown = item.get("drawdown_analysis", {})
    drawdown_html = [f"<div>{escape(drawdown.get('summary', ''))}</div>"]
    if drawdown.get("log"):
        drawdown_html.append(f"<details><summary>展开日志</summary><div>{escape(drawdown.get('log'))}</div></details>")
    cells.append(td_raw("".join(drawdown_html)))
    cells.append(td(item["remark"] or ""))
    row_class = " class=\"error\"" if not item["success"] or item["remark"] else ""
    return f"<tr{row_class} data-status=\"{escape(item['overall_status'])}\">" + "".join(cells) + "</tr>"


def td(value: Any, css_class: str = "") -> str:
    class_attr = f" class=\"{css_class}\"" if css_class else ""
    return f"<td{class_attr}>{escape(value)}</td>"


def td_raw(html_value: str, css_class: str = "") -> str:
    class_attr = f" class=\"{css_class}\"" if css_class else ""
    return f"<td{class_attr}>{html_value}</td>"


def td_number(value: Any) -> str:
    if value is None:
        return "<td data-value=\"\">N/A</td>"
    number = float(value)
    return f"<td data-value=\"{number:.4f}\">{number:.2f}</td>"


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def status_class(status: str) -> str:
    if status in {"强多头"}:
        return "strong-bull"
    if status in {"偏多"} or "线上" in status:
        return "bull"
    if status in {"强空头"}:
        return "strong-bear"
    if status in {"偏空"} or "线下" in status:
        return "bear"
    if "贴近" in status:
        return "near"
    if status == "数据不足" or status == "N/A":
        return "insufficient"
    return "neutral"


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_dir / "monitor.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )


def build_data_source(config: dict[str, Any]) -> StockDataSource:
    if str(config.get("data_source", "sina")).lower() != "sina":
        raise ValueError("only sina data_source is currently supported")
    return SinaDataSource(
        timeout_seconds=int(config["request_timeout_seconds"]),
        retry_times=int(config["retry_times"]),
    )


def run(config_path: Path, stocks_path: Path) -> Path:
    setup_logging()
    config = read_config(config_path)
    stocks = read_stocks(stocks_path)
    if not stocks:
        raise ValueError(f"no stocks found in {stocks_path}")
    source = build_data_source(config)
    windows = [int(item) for item in config["ma_windows"]]
    threshold_pct = float(config["near_threshold_pct"])
    history_limit = config.get("history_limit", "all")

    results: list[dict[str, Any]] = []
    latest_seen: str | None = None
    for stock in stocks:
        try:
            result = analyze_stock(stock, source, windows, threshold_pct, latest_seen, history_limit)
            if result.get("latest_trade_date"):
                latest_seen = max(latest_seen or result["latest_trade_date"], result["latest_trade_date"])
        except (URLError, TimeoutError, RuntimeError, ValueError) as exc:
            logging.exception("stock failed: code=%s market=%s", stock.code, stock.market)
            result = failed_result(stock, f"接口失败：{exc}")
        results.append(result)

    global_latest = max((item["latest_trade_date"] for item in results if item.get("latest_trade_date")), default=None)
    if global_latest:
        for item in results:
            if item["success"] and item["latest_trade_date"] < global_latest and "疑似停牌或未更新" not in item["remark"]:
                item["remark"] = "；".join(part for part in [item["remark"], "疑似停牌或未更新"] if part)

    output_path = Path(str(config["output_path"]))
    render_html(results, config, output_path, source.name)
    logging.info("report generated: %s success=%s failed=%s", output_path, sum(1 for item in results if item["success"]), sum(1 for item in results if not item["success"]))
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
