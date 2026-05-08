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

## 用例边界

本服务的对外 HTTP 用例由 `InvestmentAnalysisHandler.do_GET` 和 `InvestmentAnalysisHandler.do_POST` 分发。`workflow.run_analysis` 是所有分析类接口复用的核心内部用例，覆盖交割单解析、持仓周期、行为片段、问题、人格、适配度和报告生成。

## 合规边界

所有报告和风险提示仅用于投资行为复盘、风险识别和投资者教育，不构成证券、基金、期货或其他金融产品的投资建议，不输出具体买入、卖出、加仓、减仓或换股指令。
