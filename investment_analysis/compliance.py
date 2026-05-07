from __future__ import annotations

import re

PROHIBITED_PATTERNS = [
    r"建议\s*(买入|卖出|加仓|减仓)",
    r"应该\s*(买入|卖出|加仓|减仓)",
    r"目标价",
    r"保证收益",
    r"大概率上涨",
    r"必然上涨",
    r"稳赚",
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
