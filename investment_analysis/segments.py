from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from .models import BehaviorSegment, Holding, MarketBar, PositionCycle, Trade
from .utils import clamp, percent


BEHAVIOR_NAMES = {
    "LOSS_AVERAGING_DOWN": "亏损补仓",
    "CHASING_UP": "追涨买入",
    "PANIC_SELL": "杀跌卖出",
    "DISPOSITION_EFFECT": "盈利早卖/亏损久拿",
    "REBUY_AFTER_SELL": "卖出后追回",
    "CONCENTRATION": "单票重仓",
    "FREQUENT_TRADING": "频繁交易",
    "HOT_SECTOR_SWITCHING": "热点切换",
}

EMOTION_SIGNAL = {
    "LOSS_AVERAGING_DOWN": 85,
    "REBUY_AFTER_SELL": 85,
    "DISPOSITION_EFFECT": 80,
    "PANIC_SELL": 75,
    "CHASING_UP": 75,
    "CONCENTRATION": 70,
    "FREQUENT_TRADING": 70,
    "HOT_SECTOR_SWITCHING": 65,
}

DIMENSIONS = {
    "LOSS_AVERAGING_DOWN": ["回本心理", "沉没成本", "风险承受"],
    "CHASING_UP": ["FOMO", "从众", "信息来源"],
    "PANIC_SELL": ["损失厌恶", "情绪稳定性"],
    "DISPOSITION_EFFECT": ["处置效应", "亏损回避"],
    "REBUY_AFTER_SELL": ["后悔厌恶", "踏空焦虑"],
    "CONCENTRATION": ["过度自信", "集中度容忍"],
    "FREQUENT_TRADING": ["冲动性", "耐心", "策略稳定"],
    "HOT_SECTOR_SWITCHING": ["从众", "信息噪音", "主线缺失"],
}


def index_market_data(bars: list[MarketBar]) -> dict[str, list[MarketBar]]:
    grouped: dict[str, list[MarketBar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.symbol].append(bar)
    for items in grouped.values():
        items.sort(key=lambda bar: bar.date)
    return grouped


def window_return(market_index: dict[str, list[MarketBar]], symbol: str, target_date: date, days: int) -> float | None:
    bars = [bar for bar in market_index.get(symbol, []) if bar.date <= target_date]
    if len(bars) <= days:
        return None
    start = bars[-days - 1].close
    end = bars[-1].close
    return (end - start) / start if start else None


def current_position_symbols(holdings: list[Holding]) -> set[str]:
    return {holding.symbol for holding in holdings if holding.quantity > 0}


def base_scores(
    behavior_type: str,
    intensity: float,
    max_capital_used_ratio: float,
    end_date: date,
    is_current_related: bool,
    confidence: str,
    as_of: date,
    noise_penalty: float = 0.0,
) -> dict[str, float]:
    days_ago = max(0, (as_of - end_date).days)
    if days_ago <= 30:
        recency = 100
    elif days_ago <= 90:
        recency = 80
    elif days_ago <= 180:
        recency = 60
    elif days_ago <= 365:
        recency = 40
    else:
        recency = 20
    current_score = 100 if is_current_related else 20
    explainability = {"HIGH": 100, "MEDIUM": 70, "LOW": 50}.get(confidence, 50)
    capital = clamp(max_capital_used_ratio * 100 * 2.5)
    score = clamp(
        intensity * 0.30
        + capital * 0.25
        + EMOTION_SIGNAL[behavior_type] * 0.20
        + recency * 0.10
        + current_score * 0.10
        + explainability * 0.05
        - noise_penalty
    )
    return {
        "behavior_intensity_score": round(clamp(intensity), 2),
        "capital_impact_score": round(capital, 2),
        "emotion_signal_score": EMOTION_SIGNAL[behavior_type],
        "recency_score": recency,
        "current_position_score": current_score,
        "explainability_score": explainability,
        "noise_penalty": noise_penalty,
        "segment_score": round(score, 2),
    }


def make_segment(
    counter: int,
    cycle: PositionCycle,
    behavior_type: str,
    summary: str,
    evidence: dict[str, object],
    scores: dict[str, float],
    hypotheses: list[str],
    themes: list[str],
) -> BehaviorSegment:
    return BehaviorSegment(
        segment_id=f"SEG_{counter:03d}",
        user_id=cycle.user_id,
        account_id=cycle.account_id,
        behavior_type=behavior_type,
        behavior_name=BEHAVIOR_NAMES[behavior_type],
        symbol=cycle.symbol,
        stock_name=cycle.stock_name or cycle.symbol,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
        status=cycle.status,
        summary=summary,
        evidence=evidence,
        scores=scores,
        psychological_hypotheses=hypotheses,
        question_themes=themes,
        dimensions=DIMENSIONS[behavior_type],
        confidence=cycle.account_asset_confidence,
    )


def detect_loss_averaging_down(cycle: PositionCycle, as_of: date, counter: int) -> BehaviorSegment | None:
    if cycle.buy_count < 2:
        return None
    quantity = 0.0
    avg_cost = 0.0
    avg_down_count = 0
    first_loss_buy_drawdown = None
    min_drawdown = 0.0
    first_position = 0.0
    max_position = 0.0
    for trade in cycle.trades:
        if trade.side != "BUY":
            continue
        current_drawdown = (trade.price - avg_cost) / avg_cost if quantity and avg_cost else 0.0
        if quantity > 0 and current_drawdown < 0:
            avg_down_count += 1
            first_loss_buy_drawdown = first_loss_buy_drawdown if first_loss_buy_drawdown is not None else current_drawdown
        quantity += trade.quantity
        avg_cost = ((avg_cost * (quantity - trade.quantity)) + trade.quantity * trade.price + trade.fee) / quantity
        first_position = first_position or quantity
        max_position = max(max_position, quantity)
        min_drawdown = min(min_drawdown, current_drawdown)
    position_increase_ratio = max_position / first_position if first_position else 1.0
    if avg_down_count < 1 or (cycle.max_position_weight < 0.05 and position_increase_ratio < 1.5):
        return None
    max_drawdown = min(cycle.max_drawdown_pct, min_drawdown)
    intensity = min(100, avg_down_count * 20 + abs(max_drawdown) * 100 * 0.8 + position_increase_ratio * 15)
    evidence = {
        "avg_down_count": avg_down_count,
        "first_loss_buy_drawdown": first_loss_buy_drawdown,
        "max_drawdown_pct": max_drawdown,
        "position_increase_ratio": round(position_increase_ratio, 2),
        "max_position_weight": cycle.max_position_weight,
        "is_current_holding": cycle.is_current_holding,
    }
    summary = (
        f"用户在 {cycle.stock_name or cycle.symbol} 下跌过程中补仓 {avg_down_count} 次，"
        f"持仓数量扩大约 {position_increase_ratio:.1f} 倍，期间最大浮亏约 {percent(max_drawdown)}。"
    )
    scores = base_scores("LOSS_AVERAGING_DOWN", intensity, cycle.max_position_weight, cycle.end_date, cycle.is_current_holding, cycle.account_asset_confidence, as_of)
    return make_segment(counter, cycle, "LOSS_AVERAGING_DOWN", summary, evidence, scores, ["回本心理", "沉没成本偏误", "价值投资式分批买入", "仓位管理风险"], ["补仓动机", "最大仓位意识", "退出机制", "风险承受能力"])


def detect_chasing_up(cycle: PositionCycle, market_index: dict[str, list[MarketBar]], as_of: date, counter: int) -> BehaviorSegment | None:
    for trade in cycle.trades:
        if trade.side != "BUY":
            continue
        ret5 = window_return(market_index, trade.symbol, trade.trade_date.date(), 5)
        ret10 = window_return(market_index, trade.symbol, trade.trade_date.date(), 10)
        if ret5 is None and ret10 is None:
            continue
        triggered = (ret5 is not None and ret5 >= 0.08) or (ret10 is not None and ret10 >= 0.15)
        buy_ratio = trade.gross_amount / max(cycle.max_position_value, trade.gross_amount, 1.0)
        if not triggered or buy_ratio < 0.03:
            continue
        short_loss_bonus = 0.0
        intensity = (ret5 or 0) * 100 * 2 + (ret10 or 0) * 100 + buy_ratio * 100 * 1.5 + short_loss_bonus
        evidence = {
            "pre_buy_return_5d": ret5,
            "pre_buy_return_10d": ret10,
            "buy_amount_ratio": buy_ratio,
            "trade_date": trade.trade_date.date().isoformat(),
        }
        summary = (
            f"用户在买入 {cycle.stock_name or cycle.symbol} 前，股票短期已有明显上涨，"
            f"买入前 5 日涨幅约 {percent(ret5)}，10 日涨幅约 {percent(ret10)}。"
        )
        scores = base_scores("CHASING_UP", intensity, buy_ratio, trade.trade_date.date(), cycle.is_current_holding, "MEDIUM", as_of)
        return make_segment(counter, cycle, "CHASING_UP", summary, evidence, scores, ["害怕错过机会", "热点追逐", "趋势确认", "信息来源受市场情绪影响"], ["买入前研究", "趋势确认或怕错过", "信息来源", "退出规则"])
    return None


def detect_concentration(cycle: PositionCycle, as_of: date, counter: int) -> BehaviorSegment | None:
    if cycle.max_position_weight < 0.20:
        return None
    intensity = min(100, cycle.max_position_weight * 100 * 2 + min(cycle.hold_days, 120) * 0.2 + abs(cycle.realized_pnl_pct) * 100)
    evidence = {
        "max_position_weight": cycle.max_position_weight,
        "concentration_days": cycle.hold_days,
        "pnl_impact_pct": cycle.realized_pnl_pct,
        "is_current_holding": cycle.is_current_holding,
    }
    summary = (
        f"用户在 {cycle.stock_name or cycle.symbol} 上出现较高单票仓位，"
        f"最高仓位约 {percent(cycle.max_position_weight)}，持续约 {cycle.hold_days} 天。"
    )
    scores = base_scores("CONCENTRATION", intensity, cycle.max_position_weight, cycle.end_date, cycle.is_current_holding, cycle.account_asset_confidence, as_of)
    return make_segment(counter, cycle, "CONCENTRATION", summary, evidence, scores, ["高确定性信念", "过度自信", "仓位管理不足", "风险集中但未感知"], ["仓位意识", "单票仓位上限", "重仓依据", "下跌承受能力"])


def detect_rebuy_after_sell(cycle: PositionCycle, as_of: date, counter: int) -> BehaviorSegment | None:
    sells = [trade for trade in cycle.trades if trade.side == "SELL"]
    buys = [trade for trade in cycle.trades if trade.side == "BUY"]
    for sell in sells:
        for buy in buys:
            days = (buy.trade_date.date() - sell.trade_date.date()).days
            if 0 < days <= 20 and buy.price >= sell.price * 1.03:
                gap = (buy.price - sell.price) / sell.price
                intensity = min(100, (20 - days) * 2 + gap * 100 * 2 + 15)
                evidence = {"repurchase_days": days, "buyback_price_gap_pct": gap, "sell_price": sell.price, "buyback_price": buy.price}
                summary = f"用户卖出 {cycle.stock_name or cycle.symbol} 后 {days} 天又以更高价格买回，买回价较卖出价高约 {percent(gap)}。"
                scores = base_scores("REBUY_AFTER_SELL", intensity, cycle.max_position_weight, buy.trade_date.date(), cycle.is_current_holding, cycle.account_asset_confidence, as_of)
                return make_segment(counter, cycle, "REBUY_AFTER_SELL", summary, evidence, scores, ["后悔厌恶", "害怕踏空", "策略摇摆"], ["重新买入原因", "交易计划", "重新买入条件", "价格上涨后的判断变化"])
    return None


def detect_disposition_effect(cycles: list[PositionCycle], as_of: date, counter: int) -> BehaviorSegment | None:
    closed = [cycle for cycle in cycles if cycle.status == "CLOSED"]
    winners = [cycle for cycle in closed if cycle.realized_pnl_pct > 0]
    losers = [cycle for cycle in closed if cycle.realized_pnl_pct < 0]
    if len(winners) < 3 or len(losers) < 3:
        return None
    avg_win = sum(cycle.hold_days for cycle in winners) / len(winners)
    avg_loss = sum(cycle.hold_days for cycle in losers) / len(losers)
    ratio = avg_loss / max(avg_win, 1)
    small_profit_ratio = sum(1 for cycle in winners if cycle.realized_pnl_pct <= 0.05) / len(winners)
    long_loss_ratio = sum(1 for cycle in losers if cycle.hold_days >= 60 or cycle.max_drawdown_pct <= -0.10) / len(losers)
    if ratio < 2 and not (small_profit_ratio >= 0.5 and long_loss_ratio >= 0.3):
        return None
    sample = closed[-1]
    intensity = min(100, ratio * 20 + small_profit_ratio * 100 * 0.4 + long_loss_ratio * 100 * 0.4)
    evidence = {"avg_win_hold_days": avg_win, "avg_loss_hold_days": avg_loss, "win_loss_hold_ratio": ratio, "small_profit_sell_ratio": small_profit_ratio, "long_loss_hold_ratio": long_loss_ratio}
    summary = f"用户盈利交易平均持有约 {avg_win:.0f} 天，亏损交易平均持有约 {avg_loss:.0f} 天，呈现盈利较快兑现、亏损持有更久的特征。"
    scores = base_scores("DISPOSITION_EFFECT", intensity, 0.2, sample.end_date, False, "LOW", as_of)
    return make_segment(counter, sample, "DISPOSITION_EFFECT", summary, evidence, scores, ["落袋为安", "害怕利润回吐", "回避亏损确认"], ["盈利卖出原因", "亏损继续持有原因", "统一退出规则", "价值持有或被动套牢"])


def detect_frequent_trading(trades: list[Trade], cycles: list[PositionCycle], as_of: date, counter: int) -> BehaviorSegment | None:
    active = [trade for trade in trades if trade.active_trade]
    if not active:
        return None
    span_days = max(1, (max(t.trade_date for t in active) - min(t.trade_date for t in active)).days)
    active_30d = len([trade for trade in active if (as_of - trade.trade_date.date()).days <= 30])
    avg_hold = sum(cycle.hold_days for cycle in cycles) / max(len(cycles), 1)
    monthly_trades = len(active) / max(span_days / 30, 1)
    if monthly_trades < 20 and avg_hold > 10 and active_30d < 20:
        return None
    sample = cycles[-1]
    intensity = min(100, monthly_trades * 2 + max(0, 20 - avg_hold) * 3 + active_30d)
    evidence = {"monthly_trade_count": monthly_trades, "avg_hold_days": avg_hold, "active_trade_count_30d": active_30d, "repeated_symbol_ratio": _repeated_symbol_ratio(active)}
    summary = f"用户在样本期内交易较频繁，折算每月约 {monthly_trades:.0f} 笔主动交易，平均持仓约 {avg_hold:.0f} 天。"
    scores = base_scores("FREQUENT_TRADING", intensity, 0.2, sample.end_date, False, "LOW", as_of)
    return make_segment(counter, sample, "FREQUENT_TRADING", summary, evidence, scores, ["冲动交易", "机会焦虑", "短线策略", "执行纪律不足"], ["短线策略确认", "交易触发条件", "交易成本", "临时改变计划"])


def _repeated_symbol_ratio(trades: list[Trade]) -> float:
    counts = Counter(trade.symbol for trade in trades)
    repeated = sum(count for count in counts.values() if count > 1)
    return repeated / len(trades)


def detect_behavior_segments(
    cycles: list[PositionCycle],
    trades: list[Trade],
    market_data: list[MarketBar] | None = None,
    current_holdings: list[Holding] | None = None,
    as_of: date | None = None,
) -> list[BehaviorSegment]:
    as_of = as_of or date.today()
    market_index = index_market_data(market_data or [])
    candidates: list[BehaviorSegment] = []
    counter = 1
    for cycle in cycles:
        for detector in (
            lambda c: detect_loss_averaging_down(c, as_of, counter),
            lambda c: detect_chasing_up(c, market_index, as_of, counter),
            lambda c: detect_concentration(c, as_of, counter),
            lambda c: detect_rebuy_after_sell(c, as_of, counter),
        ):
            segment = detector(cycle)
            if segment is not None:
                candidates.append(segment)
                counter += 1
    for detector in (detect_disposition_effect,):
        segment = detector(cycles, as_of, counter)
        if segment is not None:
            candidates.append(segment)
            counter += 1
    frequent = detect_frequent_trading(trades, cycles, as_of, counter)
    if frequent:
        candidates.append(frequent)
    current_symbols = current_position_symbols(current_holdings or [])
    for segment in candidates:
        if segment.symbol in current_symbols:
            segment.scores["current_position_score"] = 100
        segment.selected = False
    return candidates


def select_representative_segments(candidates: list[BehaviorSegment], max_segments: int = 5) -> list[BehaviorSegment]:
    threshold = 50 if len(candidates) < 3 else 60
    filtered = [
        c for c in candidates
        if c.scores["segment_score"] >= threshold
        and c.scores["capital_impact_score"] >= 10
        and c.scores["explainability_score"] >= 50
        and c.scores["noise_penalty"] > -50
    ]
    filtered.sort(key=lambda segment: segment.scores["segment_score"], reverse=True)
    selected: list[BehaviorSegment] = []
    behavior_counts: Counter[str] = Counter()
    selected_symbols: set[str] = set()
    covered_dimensions: set[str] = set()

    def can_add(segment: BehaviorSegment, relax: bool = False) -> bool:
        if segment in selected:
            return False
        if not relax and behavior_counts[segment.behavior_type] >= 2:
            return False
        if not relax and segment.symbol in selected_symbols and segment.scores.get("current_position_score", 0) < 100:
            return False
        return True

    for priority in (
        lambda items: sorted(items, key=lambda c: c.scores["current_position_score"], reverse=True),
        lambda items: sorted(items, key=lambda c: c.scores["capital_impact_score"], reverse=True),
        lambda items: items,
    ):
        for segment in priority(filtered):
            if len(selected) >= max_segments:
                break
            if not can_add(segment):
                continue
            dimension_gain = len(set(segment.dimensions) - covered_dimensions)
            if dimension_gain > 0 or segment.scores["segment_score"] >= 85 or len(selected) < 2:
                selected.append(segment)
                behavior_counts[segment.behavior_type] += 1
                selected_symbols.add(segment.symbol)
                covered_dimensions.update(segment.dimensions)
        if len(selected) >= max_segments:
            break

    if len(selected) < 3:
        for segment in filtered:
            if can_add(segment, relax=True):
                selected.append(segment)
            if len(selected) >= min(3, max_segments):
                break

    for segment in selected:
        segment.selected = True
    return selected[:max_segments]
