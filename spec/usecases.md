# 用例索引

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 生成依据 | README、PRD、`investment_analysis/api.py`、`investment_analysis/workflow.py` |

## 用例列表

| 编号 | 用例名称 | 类型 | 入口 | 文档 |
|---|---|---|---|---|
| uc001 | 健康检查 | HTTP GET | `/health` | `spec/usecase/uc001_health_check.md` |
| uc002 | 上传交割单并推断字段映射 | HTTP POST | `/api/v1/uploads/trade-statement` | `spec/usecase/uc002_upload_trade_statement.md` |
| uc003 | 解析交割单并生成分析产物 | HTTP POST | `/api/v1/trades/parse` | `spec/usecase/uc003_parse_trades.md` |
| uc004 | 查询解析结果 | HTTP GET | `/api/v1/trades/parse-result/{parse_job_id}` | `spec/usecase/uc004_get_parse_result.md` |
| uc005 | 一键运行完整分析 | HTTP POST | `/api/v1/analysis/run` | `spec/usecase/uc005_run_analysis.md` |
| uc006 | 生成报告索引 | HTTP POST | `/api/v1/reports/generate` | `spec/usecase/uc006_generate_report.md` |
| uc007 | 获取 Markdown 报告 | HTTP GET | `/reports/{report_id}` | `spec/usecase/uc007_get_report.md` |
| uc008 | 核心分析编排 | 内部函数 | `workflow.run_analysis` | `spec/usecase/uc008_core_analysis_workflow.md` |
| uc009 | 生成行为片段总结 | HTTP POST | `/api/v1/llm/behavior-summary` | `spec/usecase/uc009_llm_behavior_summary.md` |
| uc010 | 生成片段问题 | HTTP POST | `/api/v1/llm/questions/generate` | `spec/usecase/uc010_llm_questions_generate.md` |
| uc011 | 理解用户自由文本回答 | HTTP POST | `/api/v1/llm/answers/understand` | `spec/usecase/uc011_llm_answers_understand.md` |
| uc012 | 生成报告文本章节 | HTTP POST | `/api/v1/llm/reports/write` | `spec/usecase/uc012_llm_reports_write.md` |
| uc013 | 合规检查与安全改写 | HTTP POST | `/api/v1/llm/compliance/check` | `spec/usecase/uc013_llm_compliance_check.md` |
| uc014 | 验证码登录并创建用户 | HTTP POST | `/api/v1/auth/request-code`、`/api/v1/auth/verify-code` | `spec/usecase/uc014_auth_verify_code.md` |
| uc015 | 查询登录用户历史报告 | HTTP GET | `/api/v1/reports` | `spec/usecase/uc015_list_user_reports.md` |

## 用例边界

本服务的对外 HTTP 用例由 `InvestmentAnalysisHandler.do_GET` 和 `InvestmentAnalysisHandler.do_POST` 分发。`workflow.run_analysis` 是所有分析类接口复用的核心内部用例，覆盖交割单解析、持仓周期、行为片段、问题、人格、适配度、报告生成和 LLM 回退增强结果。`/api/v1/llm/*` 用例按 PRD 的大模型 API 设计提供行为总结、问题生成、回答理解、报告撰写和合规检查能力；当前代码使用 `template-fallback` 本地适配器，保留真实大模型接入点。用户体系采用邮箱或手机号验证码登录，登录后分析报告按用户持久化为唯一报告 ID。

## 合规边界

所有报告和风险提示仅用于投资行为复盘、风险识别和投资者教育，不构成证券、基金、期货或其他金融产品的投资建议，不输出具体买入、卖出、加仓、减仓或换股指令。
