# AI 投资人格与持仓适配分析系统

这是根据 `doc/prd_with_llm.md` 落地的 Python MVP 服务。当前实现采用“规则引擎 + 可替换 LLM 层”的结构：规则引擎负责解析、持仓周期、行为片段、评分和合规硬规则；自然语言总结、问题与报告先由可审计模板生成，后续可替换为 LLM Agent。

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
