# uc004 查询解析结果

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc004 |
| 用例名称 | 查询解析结果 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/storage.py` |

## 1. 用例概述

### 1.1 业务目标

根据 `parse_job_id` 查询已保存分析产物中的解析摘要，供前端或调用方展示交易解析状态、有效行数、无效行数、警告与无效行明细。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| HTTP | GET | `/api/v1/trades/parse-result/{parse_job_id}` | `InvestmentAnalysisHandler.do_GET` |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parse_job_id | path string | 是 | uc003 或 uc005 保存的分析产物 ID |

### 2.2 响应输出

| 字段 | 类型 | 说明 |
|---|---|---|
| status | string | `SUCCESS` 或 `FAILED` |
| total_rows | number | 总处理行数 |
| valid_rows | number | 有效交易行数 |
| invalid_rows | number | 无效行数 |
| warnings | array | 解析警告 |
| invalid_row_details | array | 无效行原因和原始行 |

## 3. 主流程

```text
1. 从 URL 末尾提取 parse_job_id。
2. 调用 Repository.get_artifact 查询分析产物。
3. 若存在，读取 payload.parse_result。
4. 返回解析结果 JSON。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 查询范围 | 当前不校验用户身份，仅按产物 ID 查询 |
| 返回内容 | 只返回 `parse_result`，不返回完整交易、画像和报告 |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 产物不存在 | `parse_job_id` 查不到 | 返回 404，错误信息为 `parse result not found` |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| artifacts | 读取 | 查询 `payload_json` 并反序列化 |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/api.py` | 路由识别和响应返回 |
| `investment_analysis/storage.py` | 分析产物读取 |

## 8. 验收标准

1. 有效 `parse_job_id` 返回解析摘要 JSON。
2. 不存在的 `parse_job_id` 返回 HTTP 404。
