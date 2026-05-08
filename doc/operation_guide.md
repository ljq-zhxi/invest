# AI 投资人格与持仓适配分析系统启动、维护、使用与排障说明

## 1. 项目概述

本项目是一个 Python MVP 服务，用于基于用户交割单和当前持仓生成投资行为画像、个性化追问、持仓适配度分析和结构化报告。

当前实现采用“规则引擎 + 可替换 LLM 层”的结构：

- 规则引擎负责交割单解析、字段映射、持仓周期构建、行为片段识别、代表性片段筛选、人格评分和持仓适配度评分。
- 报告、问题和摘要当前由可审计模板生成，后续可替换为 LLM Agent。
- HTTP 服务使用 Python 标准库 `http.server` 实现，不依赖 FastAPI。
- 数据持久化使用本地 SQLite，默认数据库文件为 `investment_analysis.db`。

重要合规边界：本系统仅用于投资行为复盘、风险识别和投资者教育，不构成任何证券、基金、期货或其他金融产品的投资建议，不输出具体买入、卖出、加仓、减仓或换股指令。

## 2. 环境要求

| 项目 | 要求 |
|---|---|
| Python | 3.11 或以上 |
| 依赖 | `pandas>=2.0`、`openpyxl>=3.1` |
| 操作系统 | macOS、Linux 或可运行 Python 3.11 的环境 |
| 数据库 | SQLite，本地文件自动创建 |
| 示例数据 | `examples/trades.csv` |

## 3. 本地启动

### 3.1 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.2 安装依赖

推荐使用项目的 `pyproject.toml` 安装：

```bash
pip install -e .
```

如果只想安装运行依赖，也可以执行：

```bash
pip install "pandas>=2.0" "openpyxl>=3.1"
```

### 3.3 运行测试

```bash
python3 -m unittest discover -s tests
```

预期输出包含：

```text
Ran 4 tests
OK
```

### 3.4 启动 HTTP 服务

```bash
python3 -m investment_analysis.api --host 127.0.0.1 --port 8000
```

启动成功后，终端会输出类似：

```text
Investment analysis service listening on http://127.0.0.1:8000
```

如果需要指定数据库文件：

```bash
python3 -m investment_analysis.api --host 127.0.0.1 --port 8000 --db investment_analysis.db
```

## 4. 快速使用

### 4.1 健康检查

```bash
curl http://127.0.0.1:8000/health
```

预期响应：

```json
{
  "status": "ok"
}
```

### 4.2 一键运行完整分析

一键接口适合本地调试和 MVP 验证。它不需要先上传文件，直接传入本地交割单路径。

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

返回结果包含：

| 字段 | 说明 |
|---|---|
| `parse_result` | 解析状态、有效行、无效行和警告 |
| `normalized_trades` | 标准化后的交易记录 |
| `position_cycles` | 按股票切分后的持仓周期 |
| `candidate_segments` | 候选行为片段 |
| `selected_segments` | 代表性行为片段 |
| `questions` | 个性化事实确认、动机追问和复盘问题 |
| `persona` | 投资人格画像和 10 维得分 |
| `suitability` | 当前持仓适配度，未提供持仓时为 `null` |
| `report` | 结构化报告和 Markdown 报告 |

一键接口会保存两个固定产物：

| 产物 ID | 类型 | 说明 |
|---|---|---|
| `JOB_DIRECT` | `ANALYSIS` | 完整分析结果 |
| `R_001` | `REPORT` | 报告对象 |

### 4.3 分步调用流程

分步流程更接近 PRD 中的产品链路。

#### 步骤 1：上传交割单并推断字段映射

```bash
curl -X POST http://127.0.0.1:8000/api/v1/uploads/trade-statement \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "U001",
    "account_id": "A001",
    "file_path": "examples/trades.csv"
  }'
```

响应示例：

```json
{
  "source_file_id": "FILE_xxxxxxxxxx",
  "upload_status": "SUCCESS",
  "suggested_field_mapping": {
    "成交日期": "trade_date",
    "证券代码": "symbol",
    "证券名称": "stock_name",
    "买卖方向": "side",
    "成交数量": "quantity",
    "成交价格": "price",
    "成交金额": "gross_amount",
    "手续费": "fee"
  }
}
```

#### 步骤 2：解析交割单并生成分析产物

```bash
curl -X POST http://127.0.0.1:8000/api/v1/trades/parse \
  -H 'Content-Type: application/json' \
  -d '{
    "source_file_id": "FILE_xxxxxxxxxx",
    "account_asset": 60000
  }'
```

响应中会返回 `parse_job_id`。

#### 步骤 3：查询解析结果

```bash
curl http://127.0.0.1:8000/api/v1/trades/parse-result/JOB_xxxxxxxxxx
```

#### 步骤 4：生成报告索引

```bash
curl -X POST http://127.0.0.1:8000/api/v1/reports/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "parse_job_id": "JOB_xxxxxxxxxx"
  }'
```

#### 步骤 5：获取 Markdown 报告

```bash
curl http://127.0.0.1:8000/reports/R_001
```

## 5. 输入数据格式

### 5.1 交割单

支持 CSV、Excel `.xls`、Excel `.xlsx`。

最小必需字段：

| 标准字段 | 示例别名 | 必填 | 说明 |
|---|---|---|---|
| `trade_date` | 成交日期、交易日期、成交时间、日期 | 是 | 成交时间 |
| `symbol` | 证券代码、股票代码、标的代码、代码 | 是 | 股票代码 |
| `side` | 买卖方向、操作、业务名称、方向 | 是 | 买入或卖出 |
| `quantity` | 成交数量、数量、发生数量 | 是 | 成交数量，必须大于 0 |
| `price` | 成交价格、价格、成交均价 | 是 | 成交价格，必须大于 0 |
| `stock_name` | 证券名称、股票名称、标的名称、名称 | 否 | 股票名称 |
| `gross_amount` | 成交金额、发生金额、金额 | 否 | 缺省使用数量乘价格 |
| `fee` | 手续费、佣金、费用 | 否 | 缺省为 0 |
| `tax` | 印花税、税费 | 否 | 缺省为 0 |
| `trade_type` | 交易类型、业务类型、摘要 | 否 | 用于识别非主动交易 |

买卖方向支持：

| 原始值 | 标准值 |
|---|---|
| 买入、证券买入、B、buy | `BUY` |
| 卖出、证券卖出、S、sell | `SELL` |

以下非主动交易会保留在解析记录中，但不参与行为片段识别：

- 分红入账
- 股息红利
- 配股
- 送股
- 转托管
- 新股中签
- 债券兑付
- 基金分红
- 系统调账

### 5.2 当前持仓

`current_holdings` 用于生成持仓适配度。未提供时，系统仍会生成历史交易行为画像，但 `suitability` 为 `null`。

必需字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `snapshot_date` | date string | 持仓快照日期 |
| `user_id` | string | 用户 ID |
| `account_id` | string | 账户 ID |
| `symbol` | string | 股票代码 |
| `quantity` | number | 当前持仓数量 |
| `market_price` | number | 当前价格 |
| `market_value` | number | 当前市值 |
| `position_weight` | number | 持仓占总资产比例 |

可选字段包括 `stock_name`、`cost_basis`、`unrealized_pnl`、`unrealized_pnl_pct`、`sector`、`currency`。

### 5.3 市场数据

`market_data` 用于增强追涨等依赖行情的行为识别。未提供市场数据时，系统仍可识别亏损补仓、单票重仓、卖出后追回、处置效应和频繁交易等行为，但部分行情依赖型行为可能无法识别。

字段包括 `symbol`、`date`、`close`，可选 `open`、`high`、`low`、`volume`、`sector`、`volatility_60d`、`max_drawdown_60d`。

## 6. 维护说明

### 6.1 目录结构

| 路径 | 说明 |
|---|---|
| `investment_analysis/api.py` | HTTP 服务入口、路由分发、请求响应处理 |
| `investment_analysis/workflow.py` | 核心分析编排 |
| `investment_analysis/parser.py` | 文件读取、字段映射、交易/持仓/行情标准化 |
| `investment_analysis/cycles.py` | 持仓周期构建 |
| `investment_analysis/segments.py` | 行为片段识别与代表性片段筛选 |
| `investment_analysis/questions.py` | 个性化问题生成、回答评分 |
| `investment_analysis/persona.py` | 投资人格画像生成 |
| `investment_analysis/suitability.py` | 当前持仓适配度分析 |
| `investment_analysis/report.py` | 结构化报告和 Markdown 报告生成 |
| `investment_analysis/compliance.py` | 合规表达检查与清洗 |
| `investment_analysis/storage.py` | SQLite 上传记录和分析产物存储 |
| `tests/test_core.py` | 核心流程测试 |
| `examples/trades.csv` | 示例交割单 |
| `doc/prd.md` | 产品需求说明 |
| `spec/` | 已生成的用例 Spec 文档 |

### 6.2 修改行为识别逻辑

行为识别集中在 `investment_analysis/segments.py`。

常见维护点：

- 新增行为类型：补充 `BEHAVIOR_NAMES`、`EMOTION_SIGNAL`、`DIMENSIONS`。
- 新增检测函数：参考 `detect_loss_averaging_down`、`detect_concentration` 等函数，返回 `BehaviorSegment`。
- 接入检测函数：在 `detect_behavior_segments` 中加入新 detector。
- 调整代表性片段筛选：修改 `select_representative_segments` 的阈值、排序和多样性规则。

修改后建议补充或更新 `tests/test_core.py`。

### 6.3 修改问题和评分

问题模板在 `investment_analysis/questions.py`。

维护点：

- `MOTIVE_TEMPLATES` 定义每种行为对应的动机追问。
- 每个选项的 `scoring` 会影响人格维度。
- `infer_free_text_tags` 根据自由文本关键词修正分数。

修改问题模板后，应检查报告展示是否仍然自然，并确保不出现具体投资建议。

### 6.4 修改人格画像

人格画像在 `investment_analysis/persona.py`。

维护点：

- `infer_behavior_scores` 定义行为证据对 10 维人格分的影响。
- `classify_persona` 定义主标签和辅助标签规则。
- `build_persona_summary` 定义画像摘要表达。

如调整人格维度，应同步修改 `investment_analysis/models.py` 中的 `PERSONA_DIMENSIONS`。

### 6.5 修改持仓适配度

持仓适配度在 `investment_analysis/suitability.py`。

维护点：

- `calculate_portfolio_metrics` 定义组合指标。
- `estimate_drawdown_tolerance` 定义基于人格的回撤承受估算。
- `analyze_suitability` 定义总分和子分。
- `generate_conflicts` 与 `generate_recommendations` 定义风险冲突和关注方向。

注意：输出只能是风险关注方向，不能变成具体买卖建议。

### 6.6 修改报告和合规

报告生成在 `investment_analysis/report.py`，合规检查在 `investment_analysis/compliance.py`。

维护要求：

- 报告必须保留免责声明。
- 避免输出“建议买入”“建议卖出”“应该加仓”“应该减仓”等表达。
- 如新增报告章节，建议先经过 `compliance_check`。

### 6.7 数据库维护

默认数据库文件为 `investment_analysis.db`，启动服务后自动创建。

当前包含两张表：

| 表 | 说明 |
|---|---|
| `uploads` | 上传文件记录 |
| `artifacts` | 分析产物和报告产物 |

开发调试时如需使用干净数据库，可以换一个 `--db` 路径启动服务，例如：

```bash
python3 -m investment_analysis.api --db /tmp/investment_analysis_dev.db
```

## 7. 常见问题与解决办法

### 7.1 `ModuleNotFoundError: No module named 'pandas'`

原因：依赖未安装或没有激活虚拟环境。

解决：

```bash
source .venv/bin/activate
pip install -e .
```

### 7.2 Excel 文件读取失败

常见原因：

- 没有安装 `openpyxl`。
- 文件后缀不是 `.xls` 或 `.xlsx`。
- 文件内容损坏或不是标准 Excel。

解决：

```bash
pip install "openpyxl>=3.1"
```

如果仍失败，先将文件另存为 CSV 后再上传。

### 7.3 `unsupported file type`

原因：当前只支持 `.csv`、`.xls`、`.xlsx`。

解决：将交割单转换为 CSV 或 Excel 文件。PDF、图片截图、券商 API 自动读取暂未实现。

### 7.4 `file_path is required for the stdlib API server`

原因：上传接口 `/api/v1/uploads/trade-statement` 缺少 `file_path`。

解决：请求体必须包含本机可访问的文件路径：

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "file_path": "examples/trades.csv"
}
```

当前 MVP 上传接口不是 multipart 上传，只接收本地路径。

### 7.5 `file not found`

原因：服务进程所在机器无法访问该路径，或相对路径不是基于当前工作目录。

解决：

- 使用绝对路径。
- 确认服务是在项目根目录启动。
- 确认文件权限可读。

示例：

```json
{
  "trade_file_path": "/Users/yourname/project/invest/examples/trades.csv"
}
```

### 7.6 `missing required field mapping`

原因：系统无法从表头推断出必填字段，例如成交日期、股票代码、买卖方向、数量或价格。

解决：

1. 检查交割单表头是否包含常见别名。
2. 在请求里显式传入 `field_mapping`。

示例：

```json
{
  "source_file_id": "FILE_xxxxxxxxxx",
  "field_mapping": {
    "日期": "trade_date",
    "代码": "symbol",
    "操作": "side",
    "数量": "quantity",
    "价格": "price",
    "金额": "gross_amount"
  }
}
```

注意：`field_mapping` 的 key 是原始文件表头，value 是标准字段名。

### 7.7 `unrecognized side`

原因：买卖方向不是系统支持的值。

当前支持：

- 买入、证券买入、B、buy
- 卖出、证券卖出、S、sell

解决：

- 在原始文件中把方向字段改为支持的值。
- 或在代码 `investment_analysis/parser.py` 的 `SIDE_MAPPING` 中补充券商特有方向值。

### 7.8 `quantity must be positive` 或 `price must be positive`

原因：交易数量或成交价格为空、为 0 或为负数。

解决：

- 检查原始交割单中相关行是否为非交易流水。
- 如是分红、配股、系统调账等非主动交易，应确保 `trade_type` 能被识别，或从分析样本中剔除。
- 如是格式问题，先清洗为正数。

### 7.9 `source_file_id not found`

原因：调用 `/api/v1/trades/parse` 前没有成功执行上传，或使用了另一个数据库文件启动服务。

解决：

- 先调用 `/api/v1/uploads/trade-statement` 获取新的 `source_file_id`。
- 确认上传和解析使用同一个服务进程、同一个 `--db` 文件。

### 7.10 `analysis artifact not found`

原因：调用 `/api/v1/reports/generate` 时，指定的 `parse_job_id` 不存在。

解决：

- 先调用 `/api/v1/trades/parse` 获得 `parse_job_id`。
- 如果使用一键接口，则不传 `parse_job_id`，默认读取 `JOB_DIRECT`。

### 7.11 `parse result not found` 或 `report not found`

原因：查询的分析产物或报告产物不存在。

解决：

- 确认 ID 是否正确。
- 先完成解析或报告生成。
- 确认没有更换数据库文件。

### 7.12 返回 `主动交易笔数少于 10 笔，分析可信度较低`

原因：有效主动交易样本不足。

解决：

- 上传更长时间范围的交割单。
- 检查是否大量交易被标记为非主动交易。
- 该警告不会阻断分析，但报告可信度需要谨慎解释。

### 7.13 报告没有持仓适配度

原因：请求中没有提供 `current_holdings`。

解决：在一键分析或解析请求中传入当前持仓数组，至少包含 `snapshot_date`、`user_id`、`account_id`、`symbol`、`quantity`、`market_price`、`market_value`、`position_weight`。

### 7.14 追涨行为没有被识别

原因：追涨识别依赖 `market_data` 中的历史收盘价窗口。如果没有提供市场数据，系统无法计算买入前 5 日或 10 日涨幅。

解决：

- 在请求中传入 `market_data`。
- 至少提供 `symbol`、`date`、`close`。
- 确保买入日前有足够历史行情数据。

### 7.15 服务端口被占用

现象：启动时报端口绑定失败。

解决：换一个端口启动。

```bash
python3 -m investment_analysis.api --host 127.0.0.1 --port 8001
```

### 7.16 curl 请求返回 `route not found`

原因：路径或 HTTP 方法不匹配。

检查：

| 用途 | 方法 | 路径 |
|---|---|---|
| 健康检查 | GET | `/health` |
| 上传交割单 | POST | `/api/v1/uploads/trade-statement` |
| 解析交割单 | POST | `/api/v1/trades/parse` |
| 查询解析结果 | GET | `/api/v1/trades/parse-result/{parse_job_id}` |
| 一键分析 | POST | `/api/v1/analysis/run` |
| 生成报告 | POST | `/api/v1/reports/generate` |
| 获取报告 | GET | `/reports/{report_id}` |

### 7.17 JSON 请求解析失败

原因：请求体不是合法 JSON，或 curl 字符串引号不正确。

解决：

- 确认带上请求头 `Content-Type: application/json`。
- 使用单引号包裹 JSON，JSON 内部使用双引号。
- 复杂请求可以写入临时 JSON 文件后用 `curl -d @file.json` 发送。

### 7.18 报告中出现疑似投资建议表达

原因：新增模板或文案绕过了现有合规措辞。

解决：

- 检查 `investment_analysis/report.py` 新增文案。
- 检查 `investment_analysis/compliance.py` 的禁止表达规则。
- 保持“风险提示”“适配分析”“建议关注方向”等表达，不写具体买卖、加减仓指令。

## 8. 发布或交付前检查清单

1. 执行 `python3 -m unittest discover -s tests`，确认测试通过。
2. 使用 `examples/trades.csv` 跑通一键分析。
3. 确认报告包含免责声明。
4. 确认输出不包含具体买卖建议。
5. 如改动接口，更新 `README.md` 和 `spec/usecases.md`。
6. 如改动行为识别，更新或新增对应测试。
7. 如改动字段映射，使用至少一份 CSV 和一份 Excel 样例验证。

## 9. 后续可优化方向

- 上传接口从本地 `file_path` 升级为 multipart 文件上传。
- 增加鉴权和用户隔离，避免按产物 ID 直接查询。
- 报告 ID、分析 ID 改为动态生成，避免 `JOB_DIRECT` 和 `R_001` 被覆盖。
- 增加行情数据接入，提升追涨、杀跌、热点切换等行为识别能力。
- 增加更多券商字段别名和交易类型映射。
- 将 SQLite 替换为生产数据库，并增加迁移脚本。
- 引入 API 框架和 OpenAPI 文档，降低前后端对接成本。
