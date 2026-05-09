from __future__ import annotations

import json
import os
from typing import Any
from urllib import request

from .compliance import compliance_guard
from .models import DISCLAIMER
from .utils import clamp, percent


PROMPT_VERSION = "llm-prompt-v1"
FALLBACK_MODEL_NAME = "template-fallback"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "template").strip().lower()
PROVIDER_PRESETS = {
    "openai": {
        "base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "key_env": ("LLM_API_KEY", "OPENAI_API_KEY"),
        "json_mode": True,
    },
    "openai-compatible": {
        "base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "key_env": ("LLM_API_KEY", "OPENAI_API_KEY"),
        "json_mode": False,
    },
    "deepseek": {
        "base": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "key_env": ("LLM_API_KEY", "DEEPSEEK_API_KEY"),
        "json_mode": True,
    },
    "minimax": {
        "base": "https://api.minimax.io/v1",
        "model": "MiniMax-M2.7",
        "key_env": ("LLM_API_KEY", "MINIMAX_API_KEY"),
        "json_mode": False,
    },
    "xiaomi": {
        "base": "https://api.xiaomimimo.com/v1",
        "model": "xiaomi/mimo-v2-flash",
        "key_env": ("LLM_API_KEY", "XIAOMI_API_KEY"),
        "json_mode": False,
    },
    "mimo": {
        "base": "https://api.xiaomimimo.com/v1",
        "model": "xiaomi/mimo-v2-flash",
        "key_env": ("LLM_API_KEY", "XIAOMI_API_KEY"),
        "json_mode": False,
    },
    "mino": {
        "base": "https://api.xiaomimimo.com/v1",
        "model": "xiaomi/mimo-v2-flash",
        "key_env": ("LLM_API_KEY", "XIAOMI_API_KEY"),
        "json_mode": False,
    },
}
_PROVIDER = PROVIDER_PRESETS.get(LLM_PROVIDER, PROVIDER_PRESETS["openai-compatible"])
LLM_MODEL = os.getenv("LLM_MODEL", str(_PROVIDER["model"])).strip()
LLM_API_BASE = os.getenv("LLM_API_BASE", str(_PROVIDER["base"])).rstrip("/")
LLM_API_KEY = next((os.getenv(name) for name in _PROVIDER["key_env"] if os.getenv(name)), "")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
MODEL_NAME = LLM_MODEL if LLM_PROVIDER in PROVIDER_PRESETS and LLM_PROVIDER != "template" and LLM_API_KEY else FALLBACK_MODEL_NAME

MOTIVE_LABELS = {
    "FUNDAMENTAL_REASONING",
    "PLANNED_POSITION_BUILDING",
    "BREAKEVEN_MENTALITY",
    "AVERAGE_COST_MENTALITY",
    "FOMO",
    "HERDING",
    "PANIC_SELLING",
    "DISCIPLINED_STOP_LOSS",
    "OVERCONFIDENCE",
    "REGRET_AVERSION",
    "NO_CLEAR_PLAN",
    "INFORMATION_NOISE",
    "PROFIT_PROTECTION",
    "POSITION_RISK_AWARENESS",
    "UNCERTAIN",
}


def summarize_behavior_segment(segment: dict[str, Any]) -> dict[str, Any]:
    behavior_type = str(segment.get("behavior_type") or "")
    stock_name = str(segment.get("stock_name") or segment.get("symbol") or "该标的")
    evidence = segment.get("evidence") or {}
    observation = str(segment.get("summary") or "")
    potential_risk = "这类行为需要结合事前计划、仓位规则和风险承受能力一起复盘。"

    if behavior_type == "LOSS_AVERAGING_DOWN":
        observation = (
            f"你在 {stock_name} 下跌过程中继续加仓"
            f"{_count_phrase(evidence.get('avg_down_count'))}，最高仓位约 {percent(_float_or_none(evidence.get('max_position_weight')))}，"
            f"期间最大浮亏约 {percent(_float_or_none(evidence.get('max_drawdown_pct')))}。"
        )
        potential_risk = "如果加仓缺少明确上限，单票风险可能随价格波动逐渐扩大。"
    elif behavior_type == "CONCENTRATION":
        observation = (
            f"你在 {stock_name} 上曾出现较高单票仓位，"
            f"最高仓位约 {percent(_float_or_none(evidence.get('max_position_weight')))}。"
        )
        potential_risk = "仓位较集中时，需要关注单一标的波动对整体组合的影响。"
    elif behavior_type == "REBUY_AFTER_SELL":
        observation = (
            f"你在卖出 {stock_name} 后又较快买回，买回价格相对卖出价高约 "
            f"{percent(_float_or_none(evidence.get('buyback_price_gap_pct')))}。"
        )
        potential_risk = "这种往返交易可能反映计划变化或踏空压力，需要复盘重新买入条件。"
    elif behavior_type == "FREQUENT_TRADING":
        observation = (
            f"你在样本期内交易较频繁，折算每月约 "
            f"{_number(evidence.get('monthly_trade_count'))} 笔主动交易。"
        )
        potential_risk = "频繁交易需要关注交易触发条件、成本和执行纪律。"

    safe = compliance_guard((observation + " " + potential_risk).strip())
    fallback = {
        "segment_id": segment.get("segment_id"),
        "behavior_observation": observation[:120],
        "potential_risk": potential_risk[:120],
        "tone": "neutral",
        "compliance_passed": bool(safe["passed"]),
        "source": FALLBACK_MODEL_NAME,
    }
    llm_output = _call_llm_json(
        "你是一个投资行为分析助手，只输出 JSON，不提供投资建议。",
        (
            "请根据结构化交易片段，生成中性、客观、非投资建议式的行为观察。\n"
            "必须输出字段：behavior_observation, potential_risk, tone, compliance_passed。\n"
            "要求：不评价股票好坏，不建议买卖，不创造事实，每段不超过120字。\n"
            f"输入：{_json(segment)}"
        ),
    )
    return _validated_summary(segment.get("segment_id"), llm_output, fallback)


def generate_segment_questions(segment: dict[str, Any], question_count: int = 3) -> dict[str, Any]:
    stock_name = str(segment.get("stock_name") or segment.get("symbol") or "该标的")
    behavior_type = str(segment.get("behavior_type") or "")
    summary = str(segment.get("summary") or summarize_behavior_segment(segment)["behavior_observation"])
    questions = [
        {
            "question_type": "FACT_CONFIRMATION",
            "question_text": f"系统观察到：{summary}\n这个描述是否符合你当时的交易情况？",
            "options": [
                {"key": "A", "text": "完全符合"},
                {"key": "B", "text": "基本符合"},
                {"key": "C", "text": "不太符合"},
                {"key": "D", "text": "不记得"},
            ],
        }
    ]
    motive = _motive_question(behavior_type, stock_name)
    questions.append(motive)
    questions.append(
        {
            "question_type": "REVIEW",
            "question_text": "现在回看这段交易，你认为最需要复盘的地方是什么？",
            "options": [
                {"key": "A", "text": "买入或卖出理由是否足够清晰"},
                {"key": "B", "text": "仓位控制是否符合事前规则"},
                {"key": "C", "text": "是否缺少退出或止损条件"},
                {"key": "D", "text": "信息来源是否过度受市场情绪影响"},
                {"key": "E", "text": "暂时看不出明显问题，需要更多证据"},
            ],
        }
    )
    questions = questions[: max(1, min(3, int(question_count)))]
    text = " ".join(question["question_text"] for question in questions)
    safe = compliance_guard(text)
    fallback = {
        "segment_id": segment.get("segment_id"),
        "questions": questions,
        "compliance_passed": bool(safe["passed"]),
        "source": FALLBACK_MODEL_NAME,
    }
    llm_output = _call_llm_json(
        "你是一个投资者行为复盘问卷设计助手，只输出 JSON，不提供投资建议。",
        (
            "请基于用户真实交易片段生成问题。必须输出 questions 数组，"
            "每个问题包含 question_type, question_text, options。"
            "问题必须基于事实，不问人格定性，不包含买卖、加减仓建议。\n"
            f"每个片段问题数量：{max(1, min(3, int(question_count)))}\n"
            f"输入片段：{_json(segment)}"
        ),
    )
    return _validated_questions(segment.get("segment_id"), llm_output, fallback)


def understand_answer(answer: dict[str, Any], question: dict[str, Any] | None = None) -> dict[str, Any]:
    free_text = str(answer.get("free_text") or "")
    selected_option = str(answer.get("selected_option") or "").upper()
    text = free_text + " " + selected_option
    motives: list[dict[str, Any]] = []
    adjustments: dict[str, float] = {}

    def add(label: str, confidence: float, deltas: dict[str, float]) -> None:
        if label not in MOTIVE_LABELS:
            return
        motives.append({"label": label, "confidence": round(max(0.0, min(1.0, confidence)), 2)})
        for dimension, delta in deltas.items():
            adjustments[dimension] = clamp(adjustments.get(dimension, 0.0) + delta, -10, 10)

    if any(keyword in text for keyword in ("回本", "摊低", "降低成本")):
        add("BREAKEVEN_MENTALITY", 0.82, {"loss_aversion": 8, "discipline": -4})
        add("AVERAGE_COST_MENTALITY", 0.76, {"loss_aversion": 5})
    if any(keyword in text for keyword in ("临时", "感觉", "没计划", "没有计划", "没有明确计划")):
        add("NO_CLEAR_PLAN", 0.8, {"discipline": -8, "trading_impulsiveness": 7})
    if any(keyword in text for keyword in ("计划", "规则", "仓位上限", "止损")) and "没有明确计划" not in text and "没计划" not in text:
        add("PLANNED_POSITION_BUILDING", 0.72, {"discipline": 8, "self_awareness": 3})
    if any(keyword in text for keyword in ("基本面", "估值", "财报", "价值")):
        add("FUNDAMENTAL_REASONING", 0.68, {"discipline": 4, "overconfidence": -2})
    if any(keyword in text for keyword in ("踏空", "错过", "追不上")):
        add("FOMO", 0.78, {"fomo_tendency": 8, "trading_impulsiveness": 3})
    if any(keyword in text for keyword in ("推荐", "群", "消息", "新闻", "短视频")):
        add("INFORMATION_NOISE", 0.72, {"fomo_tendency": 5, "trading_impulsiveness": 5})
    if not motives:
        add("UNCERTAIN", 0.55 if free_text else 0.35, {})

    confidence = max(item["confidence"] for item in motives) if motives else 0.0
    summary = "用户回答中提取到的动机标签为：" + "、".join(item["label"] for item in motives)
    fallback = {
        "question_id": answer.get("question_id") or (question or {}).get("question_id"),
        "motives": motives,
        "summary": summary,
        "persona_adjustments": {key: round(value, 2) for key, value in adjustments.items()},
        "confidence": round(confidence, 2),
        "source": FALLBACK_MODEL_NAME,
    }
    llm_output = _call_llm_json(
        "你是一个投资行为文本理解助手，只输出 JSON，不提供投资建议。",
        (
            "请理解用户回答并提取行为动机标签。必须输出 motives, summary, "
            "persona_adjustments, confidence。persona_adjustments 单维度必须在 -10 到 10。\n"
            f"可选动机标签：{', '.join(sorted(MOTIVE_LABELS))}\n"
            f"问题上下文：{_json(question or {})}\n"
            f"用户回答：{_json(answer)}"
        ),
    )
    return _validated_answer(answer.get("question_id") or (question or {}).get("question_id"), llm_output, fallback)


def write_report_sections(analysis_result: dict[str, Any]) -> dict[str, Any]:
    persona = analysis_result.get("persona") or {}
    suitability = analysis_result.get("suitability") or {}
    report = analysis_result.get("report") or {}
    selected_segments = analysis_result.get("selected_segments") or []
    risk_conflicts = (suitability.get("risk_conflicts") if isinstance(suitability, dict) else None) or []
    summary = (report.get("report") or {}).get("summary") if isinstance(report.get("report"), dict) else None
    executive_summary = summary or persona.get("summary") or "本次报告基于规则引擎结果生成，用于投资行为复盘和风险识别。"
    behavior_lines = [
        summarize_behavior_segment(segment)["behavior_observation"]
        for segment in selected_segments[:5]
        if isinstance(segment, dict)
    ]
    portfolio_text = "未提供当前持仓，本次不生成持仓适配度。"
    if isinstance(suitability, dict) and suitability.get("scores"):
        score = suitability["scores"].get("overall_suitability_score")
        portfolio_text = f"当前持仓与画像的总体适配度为 {score}/100，需要结合风险冲突逐项复盘。"
    safe = compliance_guard("\n".join([executive_summary, portfolio_text, *behavior_lines]))
    fallback = {
        "executive_summary": executive_summary,
        "persona_section": persona.get("summary", ""),
        "behavior_evidence_section": "\n".join(behavior_lines),
        "portfolio_suitability_section": portfolio_text,
        "risk_reminders": risk_conflicts,
        "education_suggestions": _education_suggestions(selected_segments),
        "disclaimer": DISCLAIMER,
        "compliance_passed": bool(safe["passed"]),
        "source": FALLBACK_MODEL_NAME,
    }
    llm_output = _call_llm_json(
        "你是一个投资行为复盘报告撰写助手，只输出 JSON，不提供投资建议。",
        (
            "请根据系统计算结果生成报告章节。必须输出 executive_summary, persona_section, "
            "behavior_evidence_section, portfolio_suitability_section, risk_reminders, "
            "education_suggestions, disclaimer。不得新增事实，不得预测价格或收益。\n"
            f"输入：{_json(analysis_result)}"
        ),
    )
    return _validated_report(llm_output, fallback)


def build_llm_enrichment(analysis_result: dict[str, Any]) -> dict[str, Any]:
    selected_segments = analysis_result.get("selected_segments") or []
    questions = analysis_result.get("questions") or []
    answers = analysis_result.get("answers") or []
    question_index = {question.get("question_id"): question for question in questions if isinstance(question, dict)}
    behavior_summaries = [
        summarize_behavior_segment(segment)
        for segment in selected_segments
        if isinstance(segment, dict)
    ]
    answer_understanding = [
        understand_answer(answer, question_index.get(answer.get("question_id")))
        for answer in answers
        if isinstance(answer, dict)
    ]
    report_writing = write_report_sections(analysis_result)
    outputs = [*behavior_summaries, *answer_understanding, report_writing]
    status = "SUCCESS" if outputs and all(item.get("source") == MODEL_NAME for item in outputs if isinstance(item, dict)) and MODEL_NAME != FALLBACK_MODEL_NAME else "FALLBACK"
    return {
        "model_name": MODEL_NAME,
        "prompt_version": PROMPT_VERSION,
        "status": status,
        "behavior_summaries": behavior_summaries,
        "answer_understanding": answer_understanding,
        "report_writing": report_writing,
    }


def _motive_question(behavior_type: str, stock_name: str) -> dict[str, Any]:
    if behavior_type == "LOSS_AVERAGING_DOWN":
        text = f"当时你在 {stock_name} 下跌后继续加仓，主要原因更接近哪一种？"
        options = [
            {"key": "A", "text": "重新评估后认为价值更有吸引力"},
            {"key": "B", "text": "原本计划分批建仓，并有明确仓位上限"},
            {"key": "C", "text": "主要想降低持仓成本，等待反弹回本"},
            {"key": "D", "text": "不太愿意承认前面的判断可能有问题"},
            {"key": "E", "text": "当时没有明确计划，只是觉得跌多了会涨"},
        ]
    elif behavior_type == "CONCENTRATION":
        text = f"你当时为什么愿意在 {stock_name} 上保持较高仓位？"
        options = [
            {"key": "A", "text": "深入研究后认为确定性较高"},
            {"key": "B", "text": "符合长期核心持仓计划"},
            {"key": "C", "text": "亏损后持续补仓导致仓位变大"},
            {"key": "D", "text": "受市场热度或他人观点影响"},
            {"key": "E", "text": "当时没有意识到仓位已经偏高"},
        ]
    else:
        text = f"回看 {stock_name} 这段交易，当时最主要的决策依据是什么？"
        options = [
            {"key": "A", "text": "符合事前计划或交易系统"},
            {"key": "B", "text": "基本面或价格逻辑发生变化"},
            {"key": "C", "text": "担心错过机会或后悔之前操作"},
            {"key": "D", "text": "受到消息、群聊或市场情绪影响"},
            {"key": "E", "text": "没有明确原因，更多是临时决定"},
        ]
    return {"question_type": "MOTIVE", "question_text": text, "options": options}


def _education_suggestions(segments: list[dict[str, Any]]) -> list[str]:
    types = {str(segment.get("behavior_type")) for segment in segments if isinstance(segment, dict)}
    suggestions = ["记录交易前理由、仓位上限和退出条件，并在交易后做复盘。"]
    if "LOSS_AVERAGING_DOWN" in types:
        suggestions.append("补仓前先写明补仓条件、最大仓位和失效条件。")
    if "CONCENTRATION" in types:
        suggestions.append("重仓前做压力情景复盘，关注组合集中度风险。")
    if "FREQUENT_TRADING" in types:
        suggestions.append("频繁交易时重点记录触发条件和交易成本。")
    return suggestions[:4]


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _count_phrase(value: Any) -> str:
    number = _float_or_none(value)
    if number is None:
        return ""
    return f" {int(number)} 次"


def _number(value: Any) -> str:
    number = _float_or_none(value)
    if number is None:
        return "若干"
    return f"{number:.0f}"


def _call_llm_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    if MODEL_NAME == FALLBACK_MODEL_NAME:
        return None
    url = f"{LLM_API_BASE}/chat/completions"
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    if bool(_PROVIDER.get("json_mode")):
        payload["response_format"] = {"type": "json_object"}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=LLM_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return _parse_json_content(str(content))
    except Exception:
        return None


def _validated_summary(segment_id: Any, output: dict[str, Any] | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output, dict):
        return fallback
    observation = str(output.get("behavior_observation") or "").strip()
    risk = str(output.get("potential_risk") or "").strip()
    if not observation or not risk:
        return fallback
    safe = compliance_guard(f"{observation} {risk}")
    if not safe["passed"]:
        return fallback
    return {
        "segment_id": segment_id,
        "behavior_observation": observation[:120],
        "potential_risk": risk[:120],
        "tone": str(output.get("tone") or "neutral"),
        "compliance_passed": True,
        "source": MODEL_NAME,
    }


def _validated_questions(segment_id: Any, output: dict[str, Any] | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output, dict) or not isinstance(output.get("questions"), list):
        return fallback
    questions = []
    for item in output["questions"][:3]:
        if not isinstance(item, dict):
            continue
        question_type = str(item.get("question_type") or "").strip()
        question_text = str(item.get("question_text") or "").strip()
        options = item.get("options")
        if not question_type or not question_text or not isinstance(options, list) or not options:
            continue
        questions.append({"question_type": question_type, "question_text": question_text, "options": options})
    if not questions:
        return fallback
    safe = compliance_guard(" ".join(item["question_text"] for item in questions))
    if not safe["passed"]:
        return fallback
    return {"segment_id": segment_id, "questions": questions, "compliance_passed": True, "source": MODEL_NAME}


def _validated_answer(question_id: Any, output: dict[str, Any] | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output, dict) or not isinstance(output.get("motives"), list):
        return fallback
    motives = []
    for motive in output["motives"][:5]:
        if not isinstance(motive, dict):
            continue
        label = str(motive.get("label") or "UNCERTAIN")
        if label not in MOTIVE_LABELS:
            label = "UNCERTAIN"
        confidence = max(0.0, min(1.0, float(motive.get("confidence") or 0.0)))
        motives.append({"label": label, "confidence": round(confidence, 2)})
    adjustments = output.get("persona_adjustments") or {}
    if not isinstance(adjustments, dict):
        adjustments = {}
    bounded = {str(key): round(clamp(float(value), -10, 10), 2) for key, value in adjustments.items()}
    if not motives:
        return fallback
    return {
        "question_id": question_id,
        "motives": motives,
        "summary": str(output.get("summary") or ""),
        "persona_adjustments": bounded,
        "confidence": round(max(item["confidence"] for item in motives), 2),
        "source": MODEL_NAME,
    }


def _validated_report(output: dict[str, Any] | None, fallback: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output, dict):
        return fallback
    required = ["executive_summary", "persona_section", "behavior_evidence_section", "portfolio_suitability_section"]
    if any(not str(output.get(key) or "").strip() for key in required):
        return fallback
    safe = compliance_guard("\n".join(str(output.get(key) or "") for key in required))
    if not safe["passed"]:
        return fallback
    return {
        "executive_summary": str(output.get("executive_summary")),
        "persona_section": str(output.get("persona_section")),
        "behavior_evidence_section": str(output.get("behavior_evidence_section")),
        "portfolio_suitability_section": str(output.get("portfolio_suitability_section")),
        "risk_reminders": output.get("risk_reminders") if isinstance(output.get("risk_reminders"), list) else fallback["risk_reminders"],
        "education_suggestions": output.get("education_suggestions") if isinstance(output.get("education_suggestions"), list) else fallback["education_suggestions"],
        "disclaimer": str(output.get("disclaimer") or DISCLAIMER),
        "compliance_passed": True,
        "source": MODEL_NAME,
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _parse_json_content(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(content[start:end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None
