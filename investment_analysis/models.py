from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


PERSONA_DIMENSIONS = [
    "risk_capacity",
    "risk_preference",
    "loss_aversion",
    "fomo_tendency",
    "overconfidence",
    "trading_impulsiveness",
    "discipline",
    "holding_patience",
    "concentration_tolerance",
    "self_awareness",
]


DISCLAIMER = (
    "本报告基于用户提供的交易记录、持仓数据及系统规则生成，仅用于投资行为复盘、"
    "风险识别和投资者教育，不构成任何证券、基金、期货或其他金融产品的投资建议。"
    "报告中的风险提示不代表对任何证券价格、收益或未来表现的预测。用户应结合自身情况"
    "独立判断，必要时咨询具备资质的专业投资顾问。市场有风险，投资需谨慎。"
)


@dataclass(slots=True)
class Trade:
    trade_id: str
    user_id: str
    account_id: str
    trade_date: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    gross_amount: float
    source_file_id: str
    stock_name: str = ""
    exchange: str = ""
    settlement_date: date | None = None
    fee: float = 0.0
    tax: float = 0.0
    net_amount: float | None = None
    currency: str = "CNY"
    trade_type: str = ""
    active_trade: bool = True


@dataclass(slots=True)
class MarketBar:
    symbol: str
    date: date
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    sector: str = ""
    volatility_60d: float | None = None
    max_drawdown_60d: float | None = None


@dataclass(slots=True)
class Holding:
    snapshot_date: date
    user_id: str
    account_id: str
    symbol: str
    quantity: float
    market_price: float
    market_value: float
    position_weight: float
    stock_name: str = ""
    cost_basis: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_pct: float | None = None
    sector: str = ""
    currency: str = "CNY"


@dataclass(slots=True)
class PositionCycle:
    cycle_id: str
    user_id: str
    account_id: str
    symbol: str
    stock_name: str
    start_date: date
    end_date: date
    status: str
    trades: list[Trade] = field(default_factory=list)
    trade_count: int = 0
    buy_count: int = 0
    sell_count: int = 0
    first_buy_price: float = 0.0
    avg_buy_price: float = 0.0
    avg_sell_price: float = 0.0
    max_position_quantity: float = 0.0
    max_position_value: float = 0.0
    max_position_weight: float = 0.0
    realized_pnl: float = 0.0
    realized_pnl_pct: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown_pct: float = 0.0
    max_profit_pct: float = 0.0
    hold_days: int = 0
    is_current_holding: bool = False
    account_asset_confidence: str = "LOW"


@dataclass(slots=True)
class BehaviorSegment:
    segment_id: str
    user_id: str
    account_id: str
    behavior_type: str
    behavior_name: str
    symbol: str
    stock_name: str
    start_date: date
    end_date: date
    status: str
    summary: str
    evidence: dict[str, Any]
    scores: dict[str, float]
    psychological_hypotheses: list[str]
    question_themes: list[str]
    dimensions: list[str]
    confidence: str = "LOW"
    selected: bool = False


@dataclass(slots=True)
class Question:
    question_id: str
    segment_id: str
    question_type: str
    question_text: str
    options: list[dict[str, str]]
    scoring: dict[str, dict[str, float]]
    display_order: int


@dataclass(slots=True)
class Persona:
    persona_id: str
    user_id: str
    account_id: str
    primary_persona: str
    secondary_tags: list[str]
    scores: dict[str, float]
    summary: str
    confidence: str


@dataclass(slots=True)
class Suitability:
    suitability_id: str
    user_id: str
    account_id: str
    scores: dict[str, float]
    portfolio_metrics: dict[str, float]
    risk_conflicts: list[str]
    recommendations: list[str]
