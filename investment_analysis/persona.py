from __future__ import annotations

from .models import PERSONA_DIMENSIONS, BehaviorSegment, Persona
from .questions import score_answers
from .utils import clamp


def infer_behavior_scores(segments: list[BehaviorSegment]) -> dict[str, float]:
    scores = {dimension: 50.0 for dimension in PERSONA_DIMENSIONS}
    for segment in segments:
        strength = segment.scores.get("behavior_intensity_score", 50) / 100
        if segment.behavior_type == "LOSS_AVERAGING_DOWN":
            scores["loss_aversion"] += 30 * strength
            scores["discipline"] -= 20 * strength
            scores["overconfidence"] += 8 * strength
        elif segment.behavior_type == "CHASING_UP":
            scores["fomo_tendency"] += 30 * strength
            scores["trading_impulsiveness"] += 18 * strength
        elif segment.behavior_type == "PANIC_SELL":
            scores["loss_aversion"] += 25 * strength
            scores["holding_patience"] -= 20 * strength
        elif segment.behavior_type == "DISPOSITION_EFFECT":
            scores["loss_aversion"] += 25 * strength
            scores["discipline"] -= 15 * strength
            scores["self_awareness"] -= 10 * strength
        elif segment.behavior_type == "REBUY_AFTER_SELL":
            scores["fomo_tendency"] += 25 * strength
            scores["discipline"] -= 15 * strength
        elif segment.behavior_type == "CONCENTRATION":
            scores["concentration_tolerance"] += 30 * strength
            scores["overconfidence"] += 20 * strength
            scores["risk_preference"] += 10 * strength
        elif segment.behavior_type == "FREQUENT_TRADING":
            scores["trading_impulsiveness"] += 25 * strength
            scores["holding_patience"] -= 25 * strength
            scores["discipline"] -= 12 * strength
    return {key: clamp(value) for key, value in scores.items()}


def generate_persona(
    user_id: str,
    account_id: str,
    segments: list[BehaviorSegment],
    questions: list,
    answers: list[dict[str, str]] | None = None,
) -> Persona:
    answers = answers or []
    behavior_scores = infer_behavior_scores(segments)
    answer_deltas = score_answers(questions, answers)
    final = {}
    for dimension in PERSONA_DIMENSIONS:
        answer_score = clamp(50 + answer_deltas.get(dimension, 0.0))
        final[dimension] = round(clamp(behavior_scores[dimension] * 0.70 + answer_score * 0.30), 2)
    conflict_penalty = 0
    disputed = sum(1 for answer in answers if str(answer.get("selected_option", "")).upper() == "C")
    conflict_penalty += disputed * 8
    if final["holding_patience"] < 45 and any("长期" in str(answer.get("free_text", "")) for answer in answers):
        conflict_penalty += 15
    final["self_awareness"] = round(clamp(final["self_awareness"] - conflict_penalty), 2)
    primary, tags = classify_persona(final)
    confidence = "HIGH" if len(segments) >= 3 and len(answers) >= len(questions) * 0.7 else "MEDIUM" if segments else "LOW"
    summary = build_persona_summary(primary, final, segments)
    return Persona(
        persona_id="P_001",
        user_id=user_id,
        account_id=account_id,
        primary_persona=primary,
        secondary_tags=tags,
        scores=final,
        summary=summary,
        confidence=confidence,
    )


def classify_persona(scores: dict[str, float]) -> tuple[str, list[str]]:
    tags: list[str] = []
    if scores["loss_aversion"] >= 70 and scores["discipline"] < 55 and scores["trading_impulsiveness"] >= 60:
        primary = "情绪交易型"
    elif scores["loss_aversion"] >= 68 and scores["discipline"] < 60:
        primary = "回本补仓型"
    elif scores["fomo_tendency"] >= 70:
        primary = "机会追逐型"
    elif scores["concentration_tolerance"] >= 72 and scores["risk_preference"] >= 58:
        primary = "集中进攻型"
    elif scores["holding_patience"] >= 65 and scores["discipline"] >= 65:
        primary = "长期复利型"
    elif scores["discipline"] >= 68:
        primary = "研究驱动型"
    else:
        primary = "稳健观察型"
    if scores["loss_aversion"] >= 65:
        tags.append("损失厌恶较高")
    if scores["discipline"] < 50:
        tags.append("交易纪律偏弱")
    if scores["fomo_tendency"] >= 65:
        tags.append("踏空焦虑偏高")
    if scores["concentration_tolerance"] >= 65:
        tags.append("集中持仓容忍度较高")
    return primary, tags[:2]


def build_persona_summary(primary: str, scores: dict[str, float], segments: list[BehaviorSegment]) -> str:
    names = "、".join(sorted({segment.behavior_name for segment in segments})) or "有限交易行为"
    return (
        f"用户当前画像更接近“{primary}”。系统主要依据 {names} 等行为片段生成该结论；"
        f"损失厌恶 {scores['loss_aversion']:.0f}/100，纪律性 {scores['discipline']:.0f}/100，"
        f"踏空焦虑 {scores['fomo_tendency']:.0f}/100。结论用于风险复盘，不代表任何买卖判断。"
    )
