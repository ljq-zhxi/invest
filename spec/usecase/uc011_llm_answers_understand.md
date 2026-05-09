# uc011 理解用户自由文本回答

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc011 |
| 用例名称 | 理解用户自由文本回答 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/llm.py` |

## 1. 用例概述

从用户自由文本回答中提取行为动机标签和建议人格维度修正值。当前实现为规则关键词回退，真实 LLM 接入后仍需保持同样输出 Schema。

## 2. 输入输出

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parse_job_id | string | 否 | 分析产物 ID，用于查找问题上下文 |
| question_id | string | 是 | 问题 ID |
| selected_option | string | 否 | 用户选择 |
| free_text | string | 否 | 用户补充回答 |
| user_id | string | 否 | 无分析产物时用于任务记录 |

响应包含 `llm_task_id`、`motive_label_ids`、`motives`、`summary`、`persona_adjustments`、`confidence` 和 `source`。

## 3. 业务规则

1. 使用 PRD 中定义的动机标签，如 `BREAKEVEN_MENTALITY`、`FOMO`、`UNCERTAIN`。
2. `persona_adjustments` 单维度不得超过 -10 到 10。
3. 人格最终分仍由规则引擎融合，不由 LLM 直接决定。

## 4. 验收标准

1. “摊低成本回本”等文本可识别 `BREAKEVEN_MENTALITY`。
2. 证据不足时返回 `UNCERTAIN`。
3. 标签写入 `answer_motive_labels`。
