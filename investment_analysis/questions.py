from __future__ import annotations

from .models import BehaviorSegment, Question


FACT_OPTIONS = [
    {"key": "A", "text": "完全符合"},
    {"key": "B", "text": "基本符合"},
    {"key": "C", "text": "不太符合"},
    {"key": "D", "text": "不记得"},
]

REVIEW_OPTIONS = [
    {"key": "A", "text": "买入理由不够清晰"},
    {"key": "B", "text": "仓位控制不合理"},
    {"key": "C", "text": "没有止损或退出规则"},
    {"key": "D", "text": "信息来源不可靠"},
    {"key": "E", "text": "我认为没有明显问题，亏损主要是市场原因"},
]

MOTIVE_TEMPLATES = {
    "LOSS_AVERAGING_DOWN": (
        "当时你在 {stock_name} 下跌后继续加仓，主要原因更接近哪一种？",
        [
            {"key": "A", "text": "我重新评估后认为公司价值更有吸引力"},
            {"key": "B", "text": "我原本就计划分批建仓，并有明确仓位上限"},
            {"key": "C", "text": "我主要想降低持仓成本，等待反弹回本"},
            {"key": "D", "text": "我不愿意承认前面买错了"},
            {"key": "E", "text": "当时没有明确计划，只是觉得跌多了会涨"},
        ],
        {
            "A": {"discipline": 5, "overconfidence": -5},
            "B": {"discipline": 20, "concentration_tolerance": 10},
            "C": {"loss_aversion": 20, "discipline": -5},
            "D": {"loss_aversion": 20, "self_awareness": -10},
            "E": {"trading_impulsiveness": 15, "discipline": -15},
        },
    ),
    "CHASING_UP": (
        "你在买入 {stock_name} 前，该股票短期已经明显上涨。你当时买入的主要原因是什么？",
        [
            {"key": "A", "text": "我已长期跟踪，认为上涨验证了我的判断"},
            {"key": "B", "text": "技术趋势突破，符合我的交易系统"},
            {"key": "C", "text": "看到股价持续上涨，担心错过机会"},
            {"key": "D", "text": "看到新闻、群聊、短视频或朋友推荐"},
            {"key": "E", "text": "没有明确理由，只是感觉还会继续涨"},
        ],
        {
            "A": {"discipline": 5, "fomo_tendency": -5},
            "B": {"discipline": 15},
            "C": {"fomo_tendency": 20},
            "D": {"fomo_tendency": 15, "trading_impulsiveness": 10},
            "E": {"trading_impulsiveness": 20, "discipline": -15},
        },
    ),
    "PANIC_SELL": (
        "你在 {stock_name} 出现亏损后较快卖出。卖出时更接近下面哪种情况？",
        [
            {"key": "A", "text": "到达了事先设定的止损线"},
            {"key": "B", "text": "基本面或买入逻辑发生了变化"},
            {"key": "C", "text": "担心继续亏损，想先退出"},
            {"key": "D", "text": "看到市场情绪变差或别人也在卖"},
            {"key": "E", "text": "当时没有计划，只是不想再看到账户亏损"},
        ],
        {
            "A": {"discipline": 20},
            "B": {"discipline": 10},
            "C": {"loss_aversion": 20},
            "D": {"loss_aversion": 10, "trading_impulsiveness": 10},
            "E": {"loss_aversion": 20, "discipline": -15},
        },
    ),
    "DISPOSITION_EFFECT": (
        "系统发现你在部分交易中盈利较小时就卖出，但亏损股票持有时间更长。你卖出盈利股票时最常见的原因是什么？",
        [
            {"key": "A", "text": "达到事先设定的止盈目标"},
            {"key": "B", "text": "基本面或价格逻辑已经变化"},
            {"key": "C", "text": "觉得先落袋为安"},
            {"key": "D", "text": "害怕利润回吐"},
            {"key": "E", "text": "没有固定规则，看到赚钱就想卖"},
        ],
        {
            "A": {"discipline": 20},
            "B": {"discipline": 10},
            "C": {"loss_aversion": 15},
            "D": {"loss_aversion": 20},
            "E": {"discipline": -15, "trading_impulsiveness": 15},
        },
    ),
    "REBUY_AFTER_SELL": (
        "你曾经卖出 {stock_name} 后又在较短时间内重新买回。重新买入时的主要原因是什么？",
        [
            {"key": "A", "text": "出现了新的重要信息，改变了判断"},
            {"key": "B", "text": "价格重新触发了我的交易系统"},
            {"key": "C", "text": "卖出后上涨，担心踏空"},
            {"key": "D", "text": "后悔之前卖早了"},
            {"key": "E", "text": "没有明确原因，只是又觉得它会涨"},
        ],
        {
            "A": {"self_awareness": 10},
            "B": {"discipline": 20},
            "C": {"fomo_tendency": 20},
            "D": {"fomo_tendency": 10, "loss_aversion": 10},
            "E": {"trading_impulsiveness": 20, "discipline": -15},
        },
    ),
    "CONCENTRATION": (
        "系统发现你在 {stock_name} 上曾经出现较高仓位。你当时为什么愿意集中持有这只股票？",
        [
            {"key": "A", "text": "深入研究后认为确定性高"},
            {"key": "B", "text": "它符合我的长期核心持仓计划"},
            {"key": "C", "text": "亏损后不断补仓，仓位逐渐变大"},
            {"key": "D", "text": "受他人推荐或市场热度影响后加大投入"},
            {"key": "E", "text": "当时没有意识到仓位已经这么高"},
        ],
        {
            "A": {"overconfidence": 5, "concentration_tolerance": 10},
            "B": {"holding_patience": 20, "discipline": 10},
            "C": {"loss_aversion": 10, "discipline": -10},
            "D": {"fomo_tendency": 15, "self_awareness": -10},
            "E": {"self_awareness": -20, "discipline": -10},
        },
    ),
    "FREQUENT_TRADING": (
        "系统发现你在样本期内交易较频繁。你更接近下面哪种情况？",
        [
            {"key": "A", "text": "我本来就是短线策略，并有明确规则"},
            {"key": "B", "text": "每次买卖通常有明确触发条件"},
            {"key": "C", "text": "经常看到机会就想尝试"},
            {"key": "D", "text": "容易受市场消息或他人观点影响"},
            {"key": "E", "text": "很多交易是临时决定的"},
        ],
        {
            "A": {"discipline": 20, "holding_patience": -5},
            "B": {"discipline": 15},
            "C": {"trading_impulsiveness": 15},
            "D": {"fomo_tendency": 10, "trading_impulsiveness": 10},
            "E": {"trading_impulsiveness": 20, "discipline": -15},
        },
    ),
}


def generate_questions(segments: list[BehaviorSegment]) -> list[Question]:
    questions: list[Question] = []
    order = 1
    for segment in segments:
        questions.append(
            Question(
                question_id=f"Q{order:03d}",
                segment_id=segment.segment_id,
                question_type="FACT_CONFIRMATION",
                question_text=f"系统观察到：{segment.summary}\n这个描述是否符合你当时的交易情况？",
                options=FACT_OPTIONS,
                scoring={"A": {"observation_confidence": 20}, "B": {"observation_confidence": 10}, "C": {"observation_confidence": -20}, "D": {"observation_confidence": -10}},
                display_order=order,
            )
        )
        order += 1
        template, options, scoring = MOTIVE_TEMPLATES.get(segment.behavior_type, MOTIVE_TEMPLATES["FREQUENT_TRADING"])
        questions.append(
            Question(
                question_id=f"Q{order:03d}",
                segment_id=segment.segment_id,
                question_type="MOTIVE",
                question_text=template.format(stock_name=segment.stock_name or segment.symbol),
                options=options,
                scoring=scoring,
                display_order=order,
            )
        )
        order += 1
        questions.append(
            Question(
                question_id=f"Q{order:03d}",
                segment_id=segment.segment_id,
                question_type="REVIEW",
                question_text="现在回看这段交易，你认为最大的问题是什么？",
                options=REVIEW_OPTIONS,
                scoring={
                    "A": {"self_awareness": 15},
                    "B": {"self_awareness": 10, "discipline": 5},
                    "C": {"discipline": 15},
                    "D": {"self_awareness": 10},
                    "E": {"self_awareness": -15},
                },
                display_order=order,
            )
        )
        order += 1
    return questions[:15]


def score_answers(questions: list[Question], answers: list[dict[str, str]]) -> dict[str, float]:
    by_id = {question.question_id: question for question in questions}
    deltas: dict[str, float] = {}
    for answer in answers:
        question = by_id.get(str(answer.get("question_id")))
        if not question:
            continue
        option = str(answer.get("selected_option", "")).upper()
        for dimension, delta in question.scoring.get(option, {}).items():
            deltas[dimension] = deltas.get(dimension, 0.0) + float(delta)
        free_text = str(answer.get("free_text", "") or "")
        for dimension, delta in infer_free_text_tags(free_text).items():
            deltas[dimension] = deltas.get(dimension, 0.0) + delta
    return deltas


def infer_free_text_tags(text: str) -> dict[str, float]:
    tags: dict[str, float] = {}
    keyword_rules = [
        (("回本", "摊低", "降低成本"), "loss_aversion", 8),
        (("没计划", "临时", "感觉"), "trading_impulsiveness", 8),
        (("计划", "规则", "止损", "仓位上限"), "discipline", 8),
        (("推荐", "群", "消息", "新闻"), "fomo_tendency", 6),
        (("复盘", "反思"), "self_awareness", 6),
    ]
    for keywords, dimension, delta in keyword_rules:
        if any(keyword in text for keyword in keywords):
            tags[dimension] = tags.get(dimension, 0.0) + delta
    return tags
