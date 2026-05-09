# uc012 生成报告文本章节

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc012 |
| 用例名称 | 生成报告文本章节 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/llm.py` |

## 1. 用例概述

基于规则引擎输出的结构化结果生成自然语言报告章节。当前实现复用分析结果和模板回退，后续真实 LLM 只能改写表达，不能改写分数和事实。

## 2. 输入输出

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parse_job_id | string | 否 | 分析产物 ID，缺省为 `JOB_DIRECT` |

响应包含 `executive_summary`、`persona_section`、`behavior_evidence_section`、`portfolio_suitability_section`、`risk_reminders`、`education_suggestions`、`disclaimer` 和 `compliance_passed`。

## 3. 业务规则

1. 必须使用规则引擎给出的分数和证据。
2. 不得新增交易事实。
3. 不得预测价格、收益或评价个股好坏。
4. 必须包含免责声明。

## 4. 验收标准

1. 有效分析产物可返回报告章节。
2. 输出包含免责声明。
3. 输出不包含具体买卖建议。
