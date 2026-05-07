from __future__ import annotations

from .models import BehaviorSegment, Holding, Persona, Suitability
from .utils import clamp, percent


def calculate_portfolio_metrics(holdings: list[Holding]) -> dict[str, float]:
    if not holdings:
        return {
            "stock_count": 0,
            "max_single_position_weight": 0,
            "top3_position_weight": 0,
            "sector_concentration": 0,
            "high_volatility_weight": 0,
            "loss_position_weight": 0,
            "portfolio_max_drawdown_60d": 0.12,
            "current_unrealized_pnl_pct": 0,
        }
    weights = sorted((holding.position_weight for holding in holdings), reverse=True)
    sector_totals: dict[str, float] = {}
    loss_weight = 0.0
    unrealized = 0.0
    total_value = sum(holding.market_value for holding in holdings) or 1.0
    for holding in holdings:
        sector = holding.sector or "UNKNOWN"
        sector_totals[sector] = sector_totals.get(sector, 0.0) + holding.position_weight
        if holding.unrealized_pnl_pct is not None and holding.unrealized_pnl_pct < 0:
            loss_weight += holding.position_weight
        if holding.unrealized_pnl is not None:
            unrealized += holding.unrealized_pnl
    max_single = weights[0] if weights else 0.0
    drawdown_proxy = max(0.08, max_single * 0.45 + loss_weight * 0.10)
    return {
        "stock_count": float(len(holdings)),
        "max_single_position_weight": max_single,
        "top3_position_weight": sum(weights[:3]),
        "sector_concentration": max(sector_totals.values()) if sector_totals else 0,
        "high_volatility_weight": sum(weight for weight in weights if weight >= 0.20),
        "loss_position_weight": loss_weight,
        "portfolio_max_drawdown_60d": drawdown_proxy,
        "current_unrealized_pnl_pct": unrealized / total_value,
    }


def estimate_drawdown_tolerance(scores: dict[str, float]) -> float:
    tolerance_score = 100 - scores["loss_aversion"] * 0.4 + scores["risk_capacity"] * 0.3 + scores["risk_preference"] * 0.3
    if tolerance_score <= 30:
        return 0.08
    if tolerance_score <= 50:
        return 0.12
    if tolerance_score <= 70:
        return 0.20
    if tolerance_score <= 85:
        return 0.30
    return 0.35


def analyze_suitability(
    user_id: str,
    account_id: str,
    persona: Persona,
    holdings: list[Holding],
    segments: list[BehaviorSegment] | None = None,
) -> Suitability:
    segments = segments or []
    metrics = calculate_portfolio_metrics(holdings)
    tolerance = estimate_drawdown_tolerance(persona.scores)
    drawdown = metrics["portfolio_max_drawdown_60d"]
    if drawdown <= tolerance:
        risk_match = clamp(85 + (tolerance - drawdown) * 100)
    else:
        risk_match = clamp(85 - (drawdown - tolerance) * 300)

    behavior_penalty = 0.0
    if persona.scores["loss_aversion"] > 75 and metrics["high_volatility_weight"] > 0.5:
        behavior_penalty += 20
    if persona.scores["fomo_tendency"] > 70 and metrics["high_volatility_weight"] > 0.4:
        behavior_penalty += 15
    if persona.scores["discipline"] < 50 and metrics["max_single_position_weight"] > 0.30:
        behavior_penalty += 20
    if any(segment.behavior_type == "LOSS_AVERAGING_DOWN" and segment.scores["segment_score"] > 70 for segment in segments) and metrics["loss_position_weight"] > 0.4:
        behavior_penalty += 15
    behavior_match = clamp(100 - behavior_penalty)

    concentration_penalty = 0.0
    if metrics["max_single_position_weight"] > 0.20:
        concentration_penalty += 10
    if metrics["max_single_position_weight"] > 0.35:
        concentration_penalty += 25
    if metrics["top3_position_weight"] > 0.60:
        concentration_penalty += 15
    if metrics["sector_concentration"] > 0.50:
        concentration_penalty += 15
    if persona.scores["discipline"] < 50 and metrics["max_single_position_weight"] > 0.25:
        concentration_penalty += 10
    concentration_match = clamp(100 - concentration_penalty)

    sustainability_penalty = 0.0
    if persona.scores["loss_aversion"] > 70 and metrics["current_unrealized_pnl_pct"] < -0.10:
        sustainability_penalty += 20
    if metrics["loss_position_weight"] > 0.50:
        sustainability_penalty += 15
    if persona.scores["trading_impulsiveness"] > 65 and metrics["max_single_position_weight"] > 0.25:
        sustainability_penalty += 10
    holding_sustainability = clamp(100 - sustainability_penalty)

    overall = (
        risk_match * 0.30
        + behavior_match * 0.25
        + concentration_match * 0.20
        + holding_sustainability * 0.15
        + persona.scores["self_awareness"] * 0.10
    )
    conflicts = generate_conflicts(persona, metrics, tolerance)
    recommendations = generate_recommendations(conflicts, metrics)
    return Suitability(
        suitability_id="S_001",
        user_id=user_id,
        account_id=account_id,
        scores={
            "overall_suitability_score": round(overall, 2),
            "risk_match_score": round(risk_match, 2),
            "behavior_match_score": round(behavior_match, 2),
            "concentration_match_score": round(concentration_match, 2),
            "holding_sustainability_score": round(holding_sustainability, 2),
            "estimated_drawdown_tolerance": round(tolerance, 4),
        },
        portfolio_metrics=metrics,
        risk_conflicts=conflicts,
        recommendations=recommendations,
    )


def generate_conflicts(persona: Persona, metrics: dict[str, float], tolerance: float) -> list[str]:
    conflicts: list[str] = []
    if metrics["portfolio_max_drawdown_60d"] > tolerance:
        conflicts.append(
            f"组合回撤压力估计约 {percent(metrics['portfolio_max_drawdown_60d'])}，高于当前画像估算可承受区间 {percent(tolerance)}。"
        )
    if persona.scores["loss_aversion"] > 70 and metrics["loss_position_weight"] > 0.4:
        conflicts.append("用户损失厌恶倾向较高，而当前亏损持仓权重较高，可能放大情绪性决策压力。")
    if persona.scores["discipline"] < 55 and metrics["max_single_position_weight"] > 0.25:
        conflicts.append("交易纪律性得分偏低，同时存在较高单票仓位，需要关注临时加仓或退出规则缺失风险。")
    if metrics["sector_concentration"] > 0.5:
        conflicts.append("当前持仓行业集中度较高，组合可能受单一行业波动影响较大。")
    return conflicts or ["当前持仓未发现明显高强度适配冲突，但仍建议定期复盘仓位、波动和交易规则。"]


def generate_recommendations(conflicts: list[str], metrics: dict[str, float]) -> list[str]:
    recommendations = [
        "提前记录单票仓位上限、补仓条件和退出规则，减少市场波动时的临时决策。",
        "用比例而非绝对金额复盘风险暴露，重点关注最大单票、前三大持仓和亏损持仓权重。",
    ]
    if metrics["loss_position_weight"] > 0.4:
        recommendations.append("对亏损持仓逐一写明继续持有的条件和失效条件，区分计划内持有与被动套牢。")
    if metrics["max_single_position_weight"] > 0.25:
        recommendations.append("对重仓标的做情景压力测试，例如下跌 10% 或 20% 时是否仍能执行原计划。")
    return recommendations[:4]
