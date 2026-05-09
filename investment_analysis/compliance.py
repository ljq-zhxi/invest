from __future__ import annotations

import re

PROHIBITED_PATTERNS = [
    r"建议\s*(买入|卖出|加仓|减仓)",
    r"应该\s*(买入|卖出|加仓|减仓)",
    r"可以换成",
    r"目标价",
    r"保证收益",
    r"大概率上涨",
    r"必然上涨",
    r"稳赚",
    r"一定适合",
    r"赌徒型",
    r"韭菜型",
    r"严重心理问题",
]

REPLACEMENTS = {
    "建议买入": "建议关注相关风险",
    "建议卖出": "建议重新评估风险边界",
    "建议加仓": "建议先明确仓位规则",
    "建议减仓": "建议评估集中度风险",
    "应该买入": "可关注是否符合自身风险承受",
    "应该卖出": "可重新评估持仓理由和风险边界",
    "目标价": "价格情景",
    "保证收益": "无法承诺收益",
    "大概率上涨": "未来走势存在不确定性",
    "必然上涨": "未来走势存在不确定性",
    "稳赚": "存在投资风险",
    "可以换成": "可重新评估",
    "一定适合": "可能存在适配风险",
    "赌徒型": "高冲动交易倾向",
    "韭菜型": "经验不足倾向",
    "严重心理问题": "情绪压力较高",
}


def compliance_check(text: str) -> tuple[bool, list[str]]:
    violations = []
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, text):
            violations.append(pattern)
    return not violations, violations


def sanitize_text(text: str) -> str:
    sanitized = text
    for source, replacement in REPLACEMENTS.items():
        sanitized = sanitized.replace(source, replacement)
    return sanitized


def compliance_guard(text: str) -> dict[str, object]:
    sanitized = sanitize_text(text)
    passed, violations = compliance_check(sanitized)
    raw_passed, raw_violations = compliance_check(text)
    violation_items = [
        {
            "type": _violation_type(pattern),
            "original_text": pattern,
            "rewrite": sanitized,
        }
        for pattern in raw_violations
    ]
    return {
        "passed": passed and raw_passed,
        "violations": violation_items if violation_items else [{"type": _violation_type(pattern), "original_text": pattern, "rewrite": sanitized} for pattern in violations],
        "safe_version": sanitized,
    }


def _violation_type(pattern: str) -> str:
    if "买入" in pattern or "卖出" in pattern or "加仓" in pattern or "减仓" in pattern:
        return "INVESTMENT_ADVICE"
    if "目标价" in pattern or "上涨" in pattern:
        return "PRICE_PREDICTION"
    if "赌徒" in pattern or "韭菜" in pattern:
        return "INSULTING_LABEL"
    if "心理" in pattern:
        return "PSYCHOLOGICAL_DIAGNOSIS"
    return "COMPLIANCE_RISK"
