# uc013 合规检查与安全改写

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc013 |
| 用例名称 | 合规检查与安全改写 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/compliance.py` |

## 1. 用例概述

检查文本是否包含投资建议、收益预测、目标价、绝对化判断、侮辱性标签或不当心理诊断，并返回安全改写版本。

## 2. 输入输出

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| text | string | 是 | 待检查文本 |
| user_id | string | 否 | 任务记录用户 ID |

响应包含 `llm_task_id`、`compliance_result_id`、`passed`、`violations` 和 `safe_version`。

## 3. 主流程

```text
1. 校验 text 非空。
2. 调用 compliance_guard 执行硬规则检查和替换。
3. 写入 llm_tasks。
4. 写入 llm_compliance_results。
5. 返回 passed、violations 和 safe_version。
```

## 4. 验收标准

1. 输入“建议卖出 A 股票”时 `passed=false`。
2. `safe_version` 不包含原始违规表达。
3. 合规结果写入 `llm_compliance_results`。
