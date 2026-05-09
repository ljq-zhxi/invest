# uc009 生成行为片段总结

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc009 |
| 用例名称 | 生成行为片段总结 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/llm.py` |

## 1. 用例概述

根据规则引擎识别出的行为片段生成中性、可理解、非投资建议式的行为观察和潜在风险说明。

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parse_job_id | string | 否 | 分析产物 ID，缺省为 `JOB_DIRECT` |
| segment_id | string | 是 | 行为片段 ID |

### 2.2 响应输出

| 字段 | 类型 | 说明 |
|---|---|---|
| llm_task_id | string | LLM 任务记录 ID |
| segment_id | string | 行为片段 ID |
| behavior_observation | string | 行为观察 |
| potential_risk | string | 潜在风险提示 |
| tone | string | 当前固定为 `neutral` |
| compliance_passed | boolean | 是否通过合规检查 |
| source | string | 当前为 `template-fallback` |

## 3. 主流程

```text
1. 查询分析产物，缺省读取 JOB_DIRECT。
2. 在 selected_segments 和 candidate_segments 中查找 segment_id。
3. 调用 summarize_behavior_segment 生成行为观察。
4. 执行合规硬规则检查。
5. 写入 llm_tasks。
6. 返回结构化结果。
```

## 4. 验收标准

1. 能基于有效片段返回 `behavior_observation`。
2. 输出不包含买卖建议、目标价或收益预测。
3. 每次调用记录一条 `llm_tasks`。
