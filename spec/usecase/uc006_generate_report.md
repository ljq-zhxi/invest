# uc006 生成报告索引

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc006 |
| 用例名称 | 生成报告索引 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/storage.py` |

## 1. 用例概述

### 1.1 业务目标

将已有分析产物中的报告部分保存为独立报告产物，返回报告 ID 和访问 URL，使前端可以在分析完成后单独拉取 Markdown 报告。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| HTTP | POST | `/api/v1/reports/generate` | `InvestmentAnalysisHandler.handle_report` |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| parse_job_id | string | 否 | 分析产物 ID，缺省读取 `JOB_DIRECT` |

### 2.2 响应输出

| 字段 | 类型 | 说明 |
|---|---|---|
| report_id | string | 当前固定为 `R_001` |
| status | string | 固定为 `SUCCESS` |
| report_url | string | 当前固定为 `/reports/R_001` |

## 3. 主流程

```text
1. 从请求体读取 parse_job_id，缺省为 JOB_DIRECT。
2. 查询对应分析产物。
3. 从分析产物 payload.report 中取出报告对象。
4. 保存为 artifact_id=R_001、artifact_type=REPORT。
5. 返回报告 ID、状态和访问 URL。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 报告来源 | 必须来自已存在的分析产物 |
| 固定 ID | 报告产物固定保存为 `R_001` |
| 覆盖行为 | 多次生成会覆盖 `R_001` |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 分析产物不存在 | `parse_job_id` 查不到 | 返回 400，错误信息为 `analysis artifact not found` |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| artifacts: ANALYSIS | 读取 | 获取完整分析产物 |
| artifacts: REPORT | 写入 | 保存独立报告对象 |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/api.py` | 报告生成接口 |
| `investment_analysis/storage.py` | 产物查询与保存 |

## 8. 验收标准

1. 已存在分析产物时返回 `report_id=R_001`。
2. 返回 `report_url=/reports/R_001`。
3. 不存在的分析产物返回明确错误。
