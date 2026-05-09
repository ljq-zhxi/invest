# uc010 生成片段问题

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc010 |
| 用例名称 | 生成片段问题 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/llm.py` |

## 1. 用例概述

基于代表性行为片段生成事实确认、动机追问和事后复盘问题。当前实现使用本地模板回退，评分映射仍由规则引擎负责。

## 2. 输入输出

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parse_job_id | string | 否 | 分析产物 ID，缺省为 `JOB_DIRECT` |
| segment_ids | array | 是 | 行为片段 ID 列表 |
| question_count_per_segment | number | 否 | 每片段问题数量，默认 3，最多 3 |

响应包含 `llm_task_id`、`questionnaire_id`、`questions`、`compliance_passed` 和 `source`。

## 3. 业务规则

1. 问题必须绑定真实行为片段。
2. 不问“你是不是某类人”，重点问“当时为什么”。
3. 不包含买入、卖出、加仓、减仓建议。
4. 若未来真实 LLM 输出 Schema 不合法，应回退当前模板。

## 4. 验收标准

1. 输入有效片段后返回非空问题列表。
2. 每个问题包含 `question_type`、`question_text` 和 `options`。
3. 输出通过合规检查。
