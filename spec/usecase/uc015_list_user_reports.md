# uc015 查询登录用户历史报告

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc015 |
| 用例名称 | 查询登录用户历史报告 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/storage.py` |

## 1. 用例概述

登录用户完成一键分析后，服务生成唯一 `analysis_id` 和 `report_id` 并保存到 `artifacts`。用户可通过历史报告接口查看自己的报告列表。

## 2. 输入输出

### 请求

```http
GET /api/v1/reports
Authorization: Bearer <token>
```

### 响应

| 字段 | 类型 | 说明 |
|---|---|---|
| reports | array | 当前用户的报告列表 |
| reports[].artifact_id | string | 报告 ID |
| reports[].created_at | string | 创建时间 |
| reports[].summary | string | 报告摘要 |
| reports[].report_url | string | Markdown 报告访问地址 |

## 3. 主流程

```text
1. 从 Authorization header 中读取 Bearer token。
2. 校验 token 并查询当前用户。
3. 按 user_id 查询 artifacts 中的 REPORT 记录。
4. 按创建时间倒序返回报告摘要和访问 URL。
```

## 4. 业务规则

1. 未登录访问返回 401。
2. 只返回当前登录用户的报告。
3. 登录态分析生成的报告 ID 使用 `R_` 前缀和内容 hash 后缀，避免覆盖历史报告。

## 5. 验收标准

1. 登录后可查看历史报告列表。
2. 不同用户报告互相隔离。
3. 报告 URL 可打开对应 Markdown 报告。
