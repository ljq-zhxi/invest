# uc003 解析交割单并生成分析产物

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc003 |
| 用例名称 | 解析交割单并生成分析产物 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/workflow.py` |

## 1. 用例概述

### 1.1 业务目标

基于已上传的交割单记录运行完整分析流程，生成解析结果、标准交易、持仓周期、行为片段、问题、人格画像、可选持仓适配度和报告，并以 `parse_job_id` 持久化分析产物。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| HTTP | POST | `/api/v1/trades/parse` | `InvestmentAnalysisHandler.handle_parse` |

### 1.3 参与者

| 参与者 | 职责 |
|---|---|
| 调用方 | 提供 `source_file_id`、字段映射和可选持仓/市场/回答数据 |
| 服务端 | 查询上传记录并编排完整分析 |
| SQLite 存储 | 读取上传记录并保存分析产物 |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| source_file_id | string | 是 | 上传用例返回的文件 ID |
| field_mapping | object | 否 | 原始字段到标准字段的映射；缺省时自动推断 |
| current_holdings | array | 否 | 当前持仓列表，用于适配度分析 |
| market_data | array | 否 | 市场行情数据，用于追涨等行为识别 |
| answers | array | 否 | 用户对问题的回答，用于修正人格画像 |
| account_asset | number | 否 | 账户资产，用于仓位占比和置信度 |

### 2.2 响应输出

| 字段 | 类型 | 说明 |
|---|---|---|
| parse_job_id | string | 分析产物 ID，格式为 `JOB_` + 文件 ID 后缀 |
| status | string | 当前固定返回 `SUCCESS` |
| warnings | array | 解析过程产生的警告 |

## 3. 主流程

```text
1. 根据 source_file_id 查询 uploads。
2. 若上传记录存在，读取用户、账户、文件路径和文件 ID。
3. 调用 workflow.run_analysis。
4. run_analysis 解析交易、构建持仓周期、识别行为、生成问题与画像。
5. 如请求包含当前持仓，则生成持仓适配度。
6. 生成报告对象。
7. 使用 parse_job_id 保存完整分析产物到 artifacts。
8. 返回 parse_job_id、SUCCESS 和解析警告。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 上传依赖 | 必须先执行 uc002 获得 `source_file_id` |
| 产物类型 | 保存为 `artifact_type=ANALYSIS` |
| 交易解析 | 缺少必要字段映射会阻断；单行异常进入 `invalid_row_details` |
| 样本提醒 | 主动交易少于 10 笔时返回可信度警告 |
| 合规边界 | 分析和报告只输出风险复盘，不输出买卖指令 |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 上传记录不存在 | `source_file_id` 查不到 | 返回 400，错误信息为 `source_file_id not found` |
| 字段映射缺失 | 标准必填字段无法映射 | 返回 400，错误信息包含缺失字段 |
| 文件读取失败 | 上传记录中的文件路径失效或格式不支持 | 返回 400，错误信息透传 |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| uploads | 读取 | 获取文件路径和用户账户信息 |
| artifacts | 写入 | 保存完整分析产物，主键为 `parse_job_id` |
| parse_result | 响应与产物 | 包含总行数、有效行、无效行、警告和无效行明细 |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/api.py` | 上传记录查询、分析调用、产物保存 |
| `investment_analysis/workflow.py` | 完整分析编排 |
| `investment_analysis/parser.py` | 交易解析与校验 |
| `investment_analysis/storage.py` | 上传和产物持久化 |

## 8. 验收标准

1. 使用有效 `source_file_id` 可以返回 `parse_job_id`。
2. `artifacts` 中存在对应 `ANALYSIS` 产物。
3. 无效文件、缺失映射或不存在的 `source_file_id` 返回清晰错误。
