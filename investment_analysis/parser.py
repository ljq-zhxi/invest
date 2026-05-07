from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd

from .models import Holding, MarketBar, Trade
from .utils import parse_date, to_float


FIELD_ALIASES: dict[str, list[str]] = {
    "trade_date": ["trade_date", "成交日期", "交易日期", "成交时间", "日期"],
    "symbol": ["symbol", "证券代码", "股票代码", "标的代码", "代码"],
    "stock_name": ["stock_name", "证券名称", "股票名称", "标的名称", "名称"],
    "side": ["side", "买卖方向", "操作", "业务名称", "方向"],
    "quantity": ["quantity", "成交数量", "数量", "发生数量"],
    "price": ["price", "成交价格", "价格", "成交均价"],
    "gross_amount": ["gross_amount", "成交金额", "发生金额", "金额"],
    "fee": ["fee", "手续费", "佣金", "费用"],
    "tax": ["tax", "印花税", "税费"],
    "trade_type": ["trade_type", "交易类型", "业务类型", "摘要"],
}

SIDE_MAPPING = {
    "买入": "BUY",
    "证券买入": "BUY",
    "b": "BUY",
    "buy": "BUY",
    "卖出": "SELL",
    "证券卖出": "SELL",
    "s": "SELL",
    "sell": "SELL",
}

INACTIVE_TRADE_TYPES = {
    "分红入账",
    "股息红利",
    "配股",
    "送股",
    "转托管",
    "新股中签",
    "债券兑付",
    "基金分红",
    "系统调账",
}


def infer_field_mapping(columns: list[str]) -> dict[str, str]:
    normalized = {str(col).strip().lower(): str(col) for col in columns}
    mapping: dict[str, str] = {}
    for standard, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias.lower() in normalized:
                mapping[normalized[alias.lower()]] = standard
                break
    return mapping


def read_tabular_file(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(file_path, dtype=str)
    elif suffix in {".xlsx", ".xls"}:
        frame = pd.read_excel(file_path, dtype=str)
    else:
        raise ValueError(f"unsupported file type: {suffix}")
    frame = frame.where(pd.notnull(frame), None)
    return frame.to_dict(orient="records")


def normalize_side(value: Any) -> str:
    key = str(value).strip()
    side = SIDE_MAPPING.get(key) or SIDE_MAPPING.get(key.lower())
    if side not in {"BUY", "SELL"}:
        raise ValueError(f"unrecognized side: {value}")
    return side


def normalize_trades(
    rows: list[dict[str, Any]],
    user_id: str,
    account_id: str,
    source_file_id: str,
    field_mapping: dict[str, str] | None = None,
) -> tuple[list[Trade], list[str], list[dict[str, Any]]]:
    if not rows:
        return [], ["empty trade file"], []
    field_mapping = field_mapping or infer_field_mapping(list(rows[0].keys()))
    warnings: list[str] = []
    invalid_rows: list[dict[str, Any]] = []
    trades: list[Trade] = []

    reverse_mapping = {standard: raw for raw, standard in field_mapping.items()}
    required = ["trade_date", "symbol", "side", "quantity", "price"]
    missing = [field for field in required if field not in reverse_mapping]
    if missing:
        raise ValueError(f"missing required field mapping: {', '.join(missing)}")

    for row_index, row in enumerate(rows, start=1):
        try:
            def get(name: str, default: Any = None) -> Any:
                raw_key = reverse_mapping.get(name)
                return row.get(raw_key) if raw_key else default

            trade_date = parse_date(get("trade_date"))
            symbol = str(get("symbol")).strip()
            if not symbol:
                raise ValueError("symbol is required")
            side = normalize_side(get("side"))
            quantity = to_float(get("quantity"))
            price = to_float(get("price"))
            gross_amount = to_float(get("gross_amount"), quantity * price)
            fee = to_float(get("fee"), 0.0)
            tax = to_float(get("tax"), 0.0)
            trade_type = str(get("trade_type", "") or "").strip()
            if quantity <= 0:
                raise ValueError("quantity must be positive")
            if price <= 0:
                raise ValueError("price must be positive")
            if gross_amount < 0:
                warnings.append(f"row {row_index}: gross_amount < 0, kept for review")

            stable_key = "|".join([source_file_id, str(row_index), symbol, side, trade_date.isoformat()])
            trade_id = "T_" + hashlib.sha1(stable_key.encode("utf-8")).hexdigest()[:12].upper()
            trades.append(
                Trade(
                    trade_id=trade_id,
                    user_id=user_id,
                    account_id=account_id,
                    trade_date=trade_date,
                    symbol=symbol,
                    stock_name=str(get("stock_name", "") or ""),
                    side=side,
                    quantity=quantity,
                    price=price,
                    gross_amount=gross_amount,
                    fee=fee,
                    tax=tax,
                    net_amount=to_float(get("net_amount"), gross_amount + fee + tax),
                    trade_type=trade_type,
                    active_trade=trade_type not in INACTIVE_TRADE_TYPES,
                    source_file_id=source_file_id,
                )
            )
        except Exception as exc:
            invalid_rows.append({"row_index": row_index, "reason": str(exc), "raw": row})

    if any(trade.fee == 0 for trade in trades):
        warnings.append("部分记录缺少手续费，已按 0 处理")
    active_count = sum(1 for trade in trades if trade.active_trade)
    if active_count < 10:
        warnings.append("主动交易笔数少于 10 笔，分析可信度较低")
    return trades, warnings, invalid_rows


def parse_trade_file(
    path: str | Path,
    user_id: str,
    account_id: str,
    source_file_id: str,
    field_mapping: dict[str, str] | None = None,
) -> tuple[list[Trade], list[str], list[dict[str, Any]]]:
    return normalize_trades(read_tabular_file(path), user_id, account_id, source_file_id, field_mapping)


def normalize_holdings(rows: list[dict[str, Any]]) -> list[Holding]:
    holdings: list[Holding] = []
    for row in rows:
        holdings.append(
            Holding(
                snapshot_date=parse_date(row["snapshot_date"]).date(),
                user_id=str(row["user_id"]),
                account_id=str(row["account_id"]),
                symbol=str(row["symbol"]),
                stock_name=str(row.get("stock_name", "") or ""),
                quantity=to_float(row["quantity"]),
                market_price=to_float(row["market_price"]),
                market_value=to_float(row.get("market_value"), to_float(row["quantity"]) * to_float(row["market_price"])),
                cost_basis=to_float(row.get("cost_basis")) if row.get("cost_basis") is not None else None,
                unrealized_pnl=to_float(row.get("unrealized_pnl")) if row.get("unrealized_pnl") is not None else None,
                unrealized_pnl_pct=to_float(row.get("unrealized_pnl_pct")) if row.get("unrealized_pnl_pct") is not None else None,
                position_weight=to_float(row["position_weight"]),
                sector=str(row.get("sector", "") or ""),
            )
        )
    return holdings


def normalize_market_data(rows: list[dict[str, Any]]) -> list[MarketBar]:
    bars: list[MarketBar] = []
    for row in rows:
        bars.append(
            MarketBar(
                symbol=str(row["symbol"]),
                date=parse_date(row["date"]).date(),
                close=to_float(row["close"]),
                open=to_float(row.get("open")) if row.get("open") is not None else None,
                high=to_float(row.get("high")) if row.get("high") is not None else None,
                low=to_float(row.get("low")) if row.get("low") is not None else None,
                volume=to_float(row.get("volume")) if row.get("volume") is not None else None,
                sector=str(row.get("sector", "") or ""),
                volatility_60d=to_float(row.get("volatility_60d")) if row.get("volatility_60d") is not None else None,
                max_drawdown_60d=to_float(row.get("max_drawdown_60d")) if row.get("max_drawdown_60d") is not None else None,
            )
        )
    return bars
