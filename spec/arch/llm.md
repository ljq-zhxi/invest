# LLM 混合架构设计

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 设计依据 | `doc/prd_with_llm.md` 第 36-43 章 |

## 1. 架构原则

本服务采用“规则引擎 + 大模型”的混合架构：

| 分工 | 说明 |
|---|---|
| 规则引擎 | 负责字段校验、持仓周期、成本盈亏、行为识别、片段评分、人格评分、持仓适配评分和合规硬规则 |
| LLM 适配层 | 负责行为片段总结、问题生成、自由文本回答理解、报告章节生成和合规润色 |
| 当前实现 | 默认使用 `template-fallback` 本地模板适配器；配置真实模型环境变量后调用 OpenAI-compatible Chat Completions，内置兼容 OpenAI、DeepSeek、MiniMax、小米 MiMo/Mino |

LLM 不得作为最终投资判断主体，不得直接输出买卖建议、个股推荐、目标价、收益预测或确定性投资结论。

## 2. 当前代码落点

| 文件 | 职责 |
|---|---|
| `investment_analysis/llm.py` | LLM 适配层、OpenAI-compatible 调用、本地模板回退、结构化输出 |
| `investment_analysis/compliance.py` | 合规硬规则与安全改写 |
| `investment_analysis/api.py` | `/api/v1/llm/*` HTTP 端点 |
| `investment_analysis/storage.py` | LLM 任务、合规结果和动机标签记录 |
| `investment_analysis/workflow.py` | 在完整分析结果中追加 `llm_enrichment` |

## 3. LLM 输出与回退

| 任务 | 当前输出 | 回退状态 |
|---|---|---|
| SUMMARY | `behavior_observation`、`potential_risk`、`tone`、`compliance_passed` | `FALLBACK` |
| QUESTION | `questionnaire_id`、`questions`、`compliance_passed` | `FALLBACK` |
| ANSWER_UNDERSTANDING | `motives`、`persona_adjustments`、`confidence` | `FALLBACK` |
| REPORT | 报告摘要、画像、行为证据、持仓适配、风险提醒、投教建议、免责声明 | `FALLBACK` |
| COMPLIANCE | `passed`、`violations`、`safe_version` | `FALLBACK` |

## 4. 数据表

| 表 | 说明 |
|---|---|
| `llm_tasks` | 记录 LLM 或模板回退任务输入、输出、模型名、Prompt 版本和状态 |
| `llm_compliance_results` | 记录合规检查结果、违规项和安全改写 |
| `answer_motive_labels` | 记录回答动机标签、置信度和来源 |

## 5. 合规要求

1. 所有面向用户的 LLM 文本必须经过合规检查。
2. 合规检查不通过时，API 返回 `passed=false` 和 `safe_version`。
3. 若未来接入真实模型，模型输出必须先做 JSON Schema 校验，再进入合规检查。
4. 外部模型不可直接计算金融指标、直接判定人格、直接决定持仓适配分。

## 6. 模型配置

| 变量 | 说明 |
|---|---|
| `LLM_PROVIDER` | `template`、`openai`、`openai-compatible`、`deepseek`、`minimax`、`xiaomi`、`mimo`、`mino` |
| `LLM_MODEL` | 模型名称，如 `gpt-4o-mini`、`deepseek-chat`、`MiniMax-M2.7`、`xiaomi/mimo-v2-flash` |
| `LLM_API_KEY` | 通用模型服务 token |
| `OPENAI_API_KEY` | `LLM_API_KEY` 未配置时的备选 token |
| `DEEPSEEK_API_KEY` | DeepSeek token |
| `MINIMAX_API_KEY` | MiniMax token |
| `XIAOMI_API_KEY` | 小米 MiMo/Mino token |
| `LLM_API_BASE` | OpenAI-compatible base URL，可覆盖 provider 默认值 |
| `LLM_TIMEOUT_SECONDS` | 请求超时时间 |

默认 provider 配置：

| Provider | 默认 Base URL | 默认模型 |
|---|---|---|
| `openai` | `https://api.openai.com/v1` | `gpt-4o-mini` |
| `deepseek` | `https://api.deepseek.com` | `deepseek-chat` |
| `minimax` | `https://api.minimax.io/v1` | `MiniMax-M2.7` |
| `xiaomi` / `mimo` / `mino` | `https://api.xiaomimimo.com/v1` | `xiaomi/mimo-v2-flash` |

未配置 token、调用失败、输出 JSON 不合法或合规检查不通过时，系统回退到 `template-fallback`。
