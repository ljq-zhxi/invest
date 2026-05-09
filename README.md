# AI 投资人格与持仓适配分析系统

这是根据 `doc/prd_with_llm.md` 落地的 Python MVP 服务。当前实现采用“规则引擎 + LLM 适配层”的结构：规则引擎负责解析、持仓周期、行为片段、评分和合规硬规则；LLM 适配层负责行为总结、问题生成、自由文本理解、报告章节和合规检查。默认使用可审计的 `template-fallback` 本地模板回退；配置 `LLM_PROVIDER`、`LLM_MODEL`、`LLM_API_KEY` 后可调用 OpenAI-compatible Chat Completions。内置兼容 `openai`、`deepseek`、`minimax`、`xiaomi/mimo/mino`。

## 已实现

- CSV / Excel 交割单解析与字段别名映射
- 买卖方向标准化、非主动交易过滤、基础数据校验
- 按股票构建持仓周期，使用移动加权成本计算盈亏
- 行为片段识别：亏损补仓、追涨买入、单票重仓、卖出后追回、盈利早卖/亏损久拿、频繁交易
- 代表性片段评分与 3-5 个多样性选择
- 每个片段生成事实确认、动机追问、事后复盘问题
- 用户回答和自由文本关键词理解
- 10 维投资人格画像
- 当前持仓适配度评分、风险冲突与风险关注方向
- 合规检查和免责声明
- 简单用户验证：邮箱或手机号验证码登录，自动创建用户
- 登录用户分析报告持久化和历史报告列表
- LLM API 设计落地：行为总结、片段问题、回答理解、报告章节、合规检查
- LLM 任务、合规结果、回答动机标签的 SQLite 记录
- 标准库 HTTP API 服务，无需 FastAPI 也可运行

## 运行测试

```bash
python3 -m unittest discover -s tests
```

## 启动服务

```bash
python3 -m investment_analysis.api --host 127.0.0.1 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

浏览器界面：

```text
http://127.0.0.1:8000/
```

页面支持邮箱或手机号验证码登录、填入交割单路径、当前持仓 JSON、一键分析、查看行为片段、问题、画像、适配度、报告、历史报告和合规检查结果。

本地验证码登录：

1. `POST /api/v1/auth/request-code` 传入邮箱或手机号。
2. 当前本地版本会在响应中返回 `dev_code`，便于开发调试。
3. `POST /api/v1/auth/verify-code` 校验验证码，自动创建用户并返回 token。
4. 前端会保存 token，后续分析报告按用户持久化，可在“历史报告”标签查看。

生产环境接入短信或邮件服务后，应去掉响应里的 `dev_code`。

一键分析示例：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analysis/run \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "U001",
    "account_id": "A001",
    "trade_file_path": "examples/trades.csv",
    "account_asset": 60000,
    "current_holdings": [
      {
        "snapshot_date": "2025-05-07",
        "user_id": "U001",
        "account_id": "A001",
        "symbol": "600000",
        "stock_name": "示例银行",
        "quantity": 3000,
        "market_price": 7.8,
        "market_value": 23400,
        "position_weight": 0.39,
        "unrealized_pnl": -2500,
        "unrealized_pnl_pct": -0.1,
        "sector": "金融"
      }
    ]
  }'
```

也可以按 PRD 接口分步调用：

1. `POST /api/v1/uploads/trade-statement`
2. `POST /api/v1/trades/parse`
3. `GET /api/v1/trades/parse-result/{parse_job_id}`
4. `POST /api/v1/reports/generate`
5. `GET /reports/R_001`

当前标准库服务的上传接口接收本地 `file_path`，便于本地 MVP 验证；接入真实前端后可以替换成 multipart 上传。

LLM 适配层接口：

1. `POST /api/v1/llm/behavior-summary`
2. `POST /api/v1/llm/questions/generate`
3. `POST /api/v1/llm/answers/understand`
4. `POST /api/v1/llm/reports/write`
5. `POST /api/v1/llm/compliance/check`

详见 `doc/operation_guide.md`。

真实模型配置示例：

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o-mini
export LLM_API_KEY=你的token
# 可选，兼容 OpenAI 协议的其他服务可改 base URL
export LLM_API_BASE=https://api.openai.com/v1
```

DeepSeek：

```bash
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=你的token
export LLM_MODEL=deepseek-chat
```

MiniMax：

```bash
export LLM_PROVIDER=minimax
export MINIMAX_API_KEY=你的token
export LLM_MODEL=MiniMax-M2.7
```

小米 MiMo/Mino：

```bash
export LLM_PROVIDER=xiaomi
export XIAOMI_API_KEY=你的token
export LLM_MODEL=xiaomi/mimo-v2-flash
```
