# uc002 上传交割单并推断字段映射

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc002 |
| 用例名称 | 上传交割单并推断字段映射 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/parser.py`、`investment_analysis/storage.py` |

## 1. 用例概述

### 1.1 业务目标

接收本地交割单文件路径，校验文件存在性，生成稳定的 `source_file_id`，持久化上传记录，并根据文件表头推断标准字段映射，帮助后续解析交易记录。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| HTTP | POST | `/api/v1/uploads/trade-statement` | `InvestmentAnalysisHandler.handle_upload` |

### 1.3 参与者

| 参与者 | 职责 |
|---|---|
| 调用方 | 提供用户、账户与交割单文件路径 |
| 服务端 | 校验文件、生成文件 ID、读取表头并推断字段 |
| SQLite 存储 | 保存上传记录 |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | string | 是 | 用户 ID |
| account_id | string | 是 | 账户 ID |
| file_path | string | 是 | 本地 CSV/Excel 文件路径 |
| file_name | string | 否 | 文件名，缺省使用路径文件名 |
| file_type | string | 否 | 文件类型，缺省使用文件后缀 |

### 2.2 响应输出

| 字段 | 类型 | 说明 |
|---|---|---|
| source_file_id | string | 由用户、账户和绝对路径生成的稳定文件 ID |
| upload_status | string | 固定为 `SUCCESS` |
| suggested_field_mapping | object | 原始字段名到标准字段名的建议映射 |

## 3. 主流程

```text
1. 接收 JSON 请求体。
2. 校验 file_path 非空且文件存在。
3. 读取 user_id、account_id、file_name、file_type。
4. 使用 user_id、account_id、文件绝对路径生成 SHA1 摘要，拼接 source_file_id。
5. 调用 Repository.save_upload 保存上传记录。
6. 调用 read_tabular_file 读取 CSV/Excel 文件。
7. 基于首行字段调用 infer_field_mapping 推断标准字段映射。
8. 返回 source_file_id、上传状态和建议字段映射。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 文件类型 | 当前支持 `.csv`、`.xls`、`.xlsx` |
| 文件 ID | `FILE_` + SHA1 前 10 位大写字符 |
| 字段映射 | 支持 PRD 中定义的常见中文与英文别名 |
| MVP 限制 | 上传接口接收本地 `file_path`，不是 multipart 文件流 |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 文件路径缺失 | `file_path` 为空 | 返回 400，错误信息为 `file_path is required for the stdlib API server` |
| 文件不存在 | 路径无法在本机找到 | 返回 400，错误信息为 `file not found: ...` |
| 文件类型不支持 | 后缀不是 CSV/Excel | 返回 400，错误信息为 `unsupported file type` |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| uploads | SQLite | 保存 `source_file_id`、用户、账户、文件路径、文件类型和状态 |
| suggested_field_mapping | 响应 | 仅作为解析前建议，不单独持久化 |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/api.py` | 请求处理、文件 ID 生成、响应返回 |
| `investment_analysis/parser.py` | 表格读取与字段映射推断 |
| `investment_analysis/storage.py` | 上传记录持久化 |

## 8. 验收标准

1. 合法 CSV/Excel 路径可以返回 `source_file_id` 和 `SUCCESS`。
2. 字段别名可被推断为 `trade_date`、`symbol`、`side`、`quantity`、`price` 等标准字段。
3. 文件缺失或类型不支持时返回明确错误。
