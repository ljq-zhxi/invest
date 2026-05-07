from __future__ import annotations

from .compliance import compliance_check, sanitize_text
from .models import DISCLAIMER, BehaviorSegment, Persona, Question, Suitability


def suitability_level(score: float) -> str:
    if score >= 80:
        return "高适配"
    if score >= 65:
        return "较适配"
    if score >= 50:
        return "中等偏低"
    if score >= 35:
        return "低适配"
    return "高风险不匹配"


def generate_report(
    persona: Persona,
    segments: list[BehaviorSegment],
    questions: list[Question],
    answers: list[dict[str, str]] | None = None,
    suitability: Suitability | None = None,
) -> dict[str, object]:
    answers = answers or []
    answer_map = {answer.get("question_id"): answer for answer in answers}
    suitability_score = suitability.scores["overall_suitability_score"] if suitability else None
    sections = {
        "summary": build_summary(persona, segments, suitability_score),
        "persona": {
            "primary_persona": persona.primary_persona,
            "secondary_tags": persona.secondary_tags,
            "scores": persona.scores,
            "summary": persona.summary,
            "confidence": persona.confidence,
        },
        "representative_segments": [segment_to_report(segment) for segment in segments],
        "questions_and_answers": [
            {
                "question_id": question.question_id,
                "segment_id": question.segment_id,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "selected_option": answer_map.get(question.question_id, {}).get("selected_option"),
                "free_text": answer_map.get(question.question_id, {}).get("free_text"),
            }
            for question in questions
        ],
        "portfolio_suitability": suitability_to_report(suitability) if suitability else None,
        "behavior_risk_reminders": build_behavior_reminders(segments),
        "disclaimer": DISCLAIMER,
    }
    text = render_markdown(sections)
    text = sanitize_text(text)
    passed, violations = compliance_check(text)
    return {
        "report_id": "R_001",
        "status": "SUCCESS" if passed else "SANITIZED",
        "compliance_passed": passed,
        "compliance_violations": violations,
        "report": sections,
        "markdown": text,
    }


def build_summary(persona: Persona, segments: list[BehaviorSegment], suitability_score: float | None) -> str:
    segment_names = "、".join(segment.behavior_name for segment in segments[:5]) or "样本不足"
    if suitability_score is None:
        return f"你的投资人格更接近“{persona.primary_persona}”。系统识别出的代表性行为包括：{segment_names}。当前未提供持仓，因此本报告仅覆盖历史行为画像。"
    return (
        f"你的投资人格更接近“{persona.primary_persona}”。系统识别出的代表性行为包括：{segment_names}。"
        f"当前持仓与该画像的总体适配度为 {suitability_score:.0f}/100，属于{suitability_level(suitability_score)}。"
    )


def segment_to_report(segment: BehaviorSegment) -> dict[str, object]:
    return {
        "behavior_type": segment.behavior_type,
        "behavior_name": segment.behavior_name,
        "symbol": segment.symbol,
        "stock_name": segment.stock_name,
        "summary": segment.summary,
        "evidence": segment.evidence,
        "scores": segment.scores,
        "psychological_hypotheses": segment.psychological_hypotheses,
        "question_themes": segment.question_themes,
        "confidence": segment.confidence,
    }


def suitability_to_report(suitability: Suitability | None) -> dict[str, object] | None:
    if suitability is None:
        return None
    return {
        "scores": suitability.scores,
        "portfolio_metrics": suitability.portfolio_metrics,
        "risk_conflicts": suitability.risk_conflicts,
        "recommendations": suitability.recommendations,
    }


def build_behavior_reminders(segments: list[BehaviorSegment]) -> list[str]:
    reminders = []
    if any(segment.behavior_type == "LOSS_AVERAGING_DOWN" for segment in segments):
        reminders.append("补仓前先确认是否满足事前规则，避免仅因为下跌而扩大仓位。")
    if any(segment.behavior_type == "CHASING_UP" for segment in segments):
        reminders.append("短期上涨后买入时，记录信息来源、买入条件和退出条件。")
    if any(segment.behavior_type == "CONCENTRATION" for segment in segments):
        reminders.append("重仓前明确最大仓位和压力情景，避免集中度超出自身承受能力。")
    return reminders or ["保持交易前记录和交易后复盘，有助于提升自我认知一致性。"]


def render_markdown(sections: dict[str, object]) -> str:
    persona = sections["persona"]
    suitability = sections.get("portfolio_suitability")
    lines = [
        "# AI 投资人格与持仓适配分析报告",
        "",
        "## 1. 报告摘要",
        str(sections["summary"]),
        "",
        "## 2. 投资人格画像",
        f"主标签：{persona['primary_persona']}",
        f"辅助标签：{'、'.join(persona['secondary_tags']) or '暂无'}",
        f"画像说明：{persona['summary']}",
        "",
        "## 3. 代表性行为片段",
    ]
    for index, segment in enumerate(sections["representative_segments"], start=1):
        lines.extend([
            f"{index}. {segment['behavior_name']}：{segment['summary']}",
            f"   片段分数：{segment['scores']['segment_score']}/100，置信度：{segment['confidence']}",
        ])
    lines.extend(["", "## 4. 当前持仓适配度"])
    if suitability:
        lines.append(f"总体适配度：{suitability['scores']['overall_suitability_score']}/100，等级：{suitability_level(suitability['scores']['overall_suitability_score'])}")
        lines.append("主要风险冲突：")
        lines.extend(f"- {item}" for item in suitability["risk_conflicts"])
        lines.append("建议关注方向：")
        lines.extend(f"- {item}" for item in suitability["recommendations"])
    else:
        lines.append("未提供当前持仓，本次不生成持仓适配度。")
    lines.extend(["", "## 5. 行为偏差提醒"])
    lines.extend(f"- {item}" for item in sections["behavior_risk_reminders"])
    lines.extend(["", "## 6. 免责声明", str(sections["disclaimer"])])
    return "\n".join(lines)
