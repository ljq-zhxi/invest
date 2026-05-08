# uc005 一键运行完整分析

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc005 |
| 用例名称 | 一键运行完整分析 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/workflow.py` |

## 1. 用例概述

### 1.1 业务目标

为本地 MVP 提供单次请求完成全部分析的便捷入口。调用方直接提供交割单路径、用户账户、可选持仓、市场数据和问卷回答，服务返回完整分析结果并保存固定分析产物与报告产物。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| HTTP | POST | `/api/v1/analysis/run` | `InvestmentAnalysisHandler.handle_run_analysis` |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | string | 是 | 用户 ID |
| account_id | string | 是 | 账户 ID |
| trade_file_path | string | 是 | 本地交割单路径 |
| source_file_id | string | 否 | 来源文件 ID，缺省为 `FILE_DIRECT` |
| field_mapping | object | 否 | 字段映射 |
| current_holdings | array | 否 | 当前持仓 |
| market_data | array | 否 | 市场行情 |
| answers | array | 否 | 用户回答 |
| account_asset | number | 否 | 账户资产 |

### 2.2 响应输出

完整返回 `workflow.run_analysis` 的结果：

| 字段 | 类型 | 说明 |
|---|---|---|
| parse_result | object | 解析摘要 |
| normalized_trades | array | 标准化交易列表 |
| position_cycles | array | 持仓周期列表 |
| candidate_segments | array | 候选行为片段 |
| selected_segments | array | 代表性行为片段 |
| questions | array | 个性化问题 |
| persona | object | 投资人格画像 |
| suitability | object/null | 当前持仓适配度 |
| report | object | 结构化报告与 Markdown |

## 3. 主流程

```text
1. 接收请求体并读取用户、账户、交割单路径。
2. 设置 source_file_id，未传时使用 FILE_DIRECT。
3. 调用 workflow.run_analysis 执行完整分析。
4. 将完整结果保存为 artifact_id=JOB_DIRECT、artifact_type=ANALYSIS。
5. 将报告对象保存为 artifact_id=R_001、artifact_type=REPORT。
6. 返回完整分析结果。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 便捷入口 | 不依赖 uc002 上传记录 |
| 固定产物 ID | 分析产物固定为 `JOB_DIRECT`，报告固定为 `R_001` |
| 覆盖行为 | 多次调用会覆盖同名产物 |
| 持仓适配 | 仅当 `current_holdings` 非空时生成 |
| 合规边界 | 报告经合规检查和敏感表达清洗后返回 |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 必填字段缺失 | `user_id`、`account_id` 或 `trade_file_path` 缺失 | 返回 400，错误信息透传 |
| 文件解析失败 | 文件不存在、类型不支持或字段映射缺失 | 返回 400，错误信息透传 |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| artifacts: JOB_DIRECT | 写入 | 保存完整分析结果 |
| artifacts: R_001 | 写入 | 保存报告对象 |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/api.py` | 一键分析接口、固定产物保存 |
| `investment_analysis/workflow.py` | 完整分析编排 |
| `investment_analysis/report.py` | 报告生成与合规检查 |

## 8. 验收标准

1. 使用 README 示例请求可以返回完整分析 JSON。
2. 响应中包含 `parse_result`、`persona` 和 `report`。
3. 提供当前持仓时，响应中 `suitability` 不为空。
4. 产物 `JOB_DIRECT` 和 `R_001` 可被后续接口读取。
