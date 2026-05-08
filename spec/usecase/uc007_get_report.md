# uc007 获取 Markdown 报告

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc007 |
| 用例名称 | 获取 Markdown 报告 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/api.py`、`investment_analysis/storage.py` |

## 1. 用例概述

### 1.1 业务目标

根据报告 ID 返回已生成报告的 Markdown 文本，供浏览器、前端页面或调试工具直接展示投资人格与持仓适配分析报告。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| HTTP | GET | `/reports/{report_id}` | `InvestmentAnalysisHandler.do_GET` |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| report_id | path string | 是 | 报告产物 ID，当前主要为 `R_001` |

### 2.2 响应输出

响应类型为 `text/markdown; charset=utf-8`，正文为报告 Markdown。报告内容包括摘要、人格画像、代表性行为片段、当前持仓适配度、行为偏差提醒和免责声明。

## 3. 主流程

```text
1. 从 URL 末尾提取 report_id。
2. 查询对应报告产物。
3. 从 payload.markdown 读取 Markdown 文本。
4. 以 text/markdown 返回。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 内容来源 | 仅返回已保存报告产物中的 `markdown` 字段 |
| Content-Type | 使用 `text/markdown; charset=utf-8` |
| 合规边界 | 报告生成阶段已执行合规检查和免责声明拼接 |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 报告不存在 | `report_id` 查不到 | 返回 404，错误信息为 `report not found` |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| artifacts: REPORT | 读取 | 获取报告 Markdown |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/api.py` | Markdown 报告响应 |
| `investment_analysis/storage.py` | 报告产物读取 |
| `investment_analysis/report.py` | Markdown 生成逻辑 |

## 8. 验收标准

1. 已存在报告 ID 时返回 Markdown 文本。
2. 响应头 `Content-Type` 为 `text/markdown; charset=utf-8`。
3. 不存在的报告 ID 返回 HTTP 404。
