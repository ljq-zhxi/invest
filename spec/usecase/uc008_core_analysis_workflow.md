# uc008 核心分析编排

## 文档维护说明

| 字段 | 内容 |
|---|---|
| 服务名称 | AI 投资人格与持仓适配分析系统 |
| 用例编号 | uc008 |
| 用例名称 | 核心分析编排 |
| 维护人员 | Lei Jianqiu |
| 生成日期 | 2026-05-08 |
| 代码来源 | `investment_analysis/workflow.py` 及领域模块 |

## 1. 用例概述

### 1.1 业务目标

把交割单、当前持仓、市场数据和用户回答转换为可解释的投资行为画像与持仓适配报告。该用例是 uc003 和 uc005 共同依赖的核心领域流程。

### 1.2 触发入口

| 类型 | 方法 | 路径/函数 | 代码位置 |
|---|---|---|---|
| 内部函数 | 调用 | `workflow.run_analysis` | `investment_analysis/workflow.py` |

### 1.3 参与者

| 参与者 | 职责 |
|---|---|
| API 层 | 传入文件路径和业务上下文 |
| 解析模块 | 标准化交易、持仓和市场数据 |
| 周期模块 | 构建持仓周期 |
| 行为模块 | 识别和筛选行为片段 |
| 问题模块 | 为片段生成追问 |
| 人格模块 | 生成投资人格画像 |
| 适配模块 | 分析当前持仓与人格的适配度 |
| 报告模块 | 生成结构化报告和 Markdown |
| LLM 适配层 | 生成行为总结、回答理解和报告章节的回退增强结果 |

## 2. 输入输出

### 2.1 请求输入

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | string | 是 | 用户 ID |
| account_id | string | 是 | 账户 ID |
| trade_file_path | string/path | 是 | 交割单路径 |
| source_file_id | string | 否 | 来源文件 ID，缺省为 `FILE_001` |
| field_mapping | object | 否 | 字段映射 |
| holdings_rows | array | 否 | 当前持仓原始行 |
| market_rows | array | 否 | 市场行情原始行 |
| answers | array | 否 | 用户回答 |
| account_asset | number | 否 | 账户资产 |
| as_of | date | 否 | 分析基准日期 |

### 2.2 响应输出

| 字段 | 类型 | 说明 |
|---|---|---|
| parse_result | object | 解析状态、行数、警告和无效行 |
| normalized_trades | array | 标准化交易 |
| position_cycles | array | 持仓周期 |
| candidate_segments | array | 候选行为片段 |
| selected_segments | array | 代表性行为片段 |
| questions | array | 事实确认、动机追问和复盘问题 |
| persona | object | 人格画像、维度分和置信度 |
| suitability | object/null | 持仓适配度；未提供持仓时为空 |
| report | object | 报告结构、Markdown、合规检查结果 |
| llm_enrichment | object | LLM/模板回退增强结果，包含行为总结、回答理解和报告章节 |

## 3. 主流程

```text
1. 调用 parse_trade_file 读取并标准化交割单。
2. 调用 normalize_holdings 标准化当前持仓。
3. 调用 normalize_market_data 标准化市场行情。
4. 调用 build_position_cycles 按用户、账户、股票构建持仓周期。
5. 调用 detect_behavior_segments 识别候选行为片段。
6. 调用 select_representative_segments 选择 3-5 个代表性片段。
7. 调用 generate_questions 为每个代表性片段生成最多 3 个问题。
8. 调用 generate_persona 综合行为证据与用户回答生成人格画像。
9. 若存在当前持仓，调用 analyze_suitability 生成持仓适配度。
10. 调用 generate_report 生成结构化报告和 Markdown。
11. 调用 build_llm_enrichment 生成 LLM 回退增强结果。
12. 将所有 dataclass 转换为字典后返回。
```

## 4. 业务规则

| 规则 | 说明 |
|---|---|
| 交易标准化 | 必填字段包括成交日期、股票代码、买卖方向、数量和价格 |
| 非主动交易 | 分红、配股、转托管等不进入行为片段识别 |
| 持仓周期 | 同一股票从持仓为 0 到再次归 0 形成一个周期；未清仓周期为 `OPEN` |
| 行为识别 | 当前实现覆盖亏损补仓、追涨买入、单票重仓、卖出后追回、处置效应、频繁交易 |
| 代表性筛选 | 兼顾片段分、资金影响、当前持仓相关性、行为类型多样性和股票多样性 |
| 问题生成 | 每个片段生成事实确认、动机追问、事后复盘三类问题，总数最多 15 个 |
| 人格画像 | 基于行为片段 70% 与回答修正 30% 融合生成 10 维得分 |
| 持仓适配 | 只有提供当前持仓时才计算；主要评估风险匹配、行为匹配、集中度和可持续性 |
| 合规检查 | 报告必须包含免责声明，并清理可能构成投资建议的表达 |
| LLM 回退 | 当前使用 `template-fallback` 本地适配器，不依赖外部大模型服务 |
| LLM 边界 | LLM 只能改写表达和提取动机标签，不能直接计算指标、判定人格或决定适配分 |

## 5. 异常流程

| 场景 | 触发条件 | 当前处理 |
|---|---|---|
| 文件读取失败 | 路径不存在或类型不支持 | 异常向 API 层透传 |
| 字段映射缺失 | 标准必填字段无法得到 | 抛出 `ValueError` |
| 单行数据异常 | 数量、价格、方向等无效 | 放入 `invalid_row_details`，其他行继续处理 |
| 当前持仓缺失 | `holdings_rows` 为空 | 跳过适配度分析，`suitability=null` |

## 6. 数据与状态

| 数据对象 | 来源/去向 | 说明 |
|---|---|---|
| Trade | parser | 标准化交易记录 |
| PositionCycle | cycles | 持仓周期 |
| BehaviorSegment | segments | 候选与代表性行为片段 |
| Question | questions | 个性化问题 |
| Persona | persona | 投资人格画像 |
| Suitability | suitability | 当前持仓适配度 |
| Report | report | 报告结构和 Markdown 文本 |
| llm_enrichment | llm | 行为片段总结、回答理解、报告章节回退结果 |

## 7. 关联代码

| 文件 | 说明 |
|---|---|
| `investment_analysis/workflow.py` | 核心流程编排 |
| `investment_analysis/parser.py` | 文件读取、字段映射、交易/持仓/行情标准化 |
| `investment_analysis/cycles.py` | 持仓周期构建 |
| `investment_analysis/segments.py` | 行为片段识别与筛选 |
| `investment_analysis/questions.py` | 个性化问题生成和回答评分 |
| `investment_analysis/persona.py` | 人格画像生成 |
| `investment_analysis/suitability.py` | 持仓适配度分析 |
| `investment_analysis/report.py` | 报告生成与合规处理 |
| `investment_analysis/llm.py` | LLM 适配层与模板回退 |

## 8. 验收标准

1. 示例交割单可以生成非空 `normalized_trades` 和 `position_cycles`。
2. 存在典型交易行为时可以识别并筛选代表性片段。
3. 每个代表性片段生成事实确认、动机追问和复盘问题。
4. 提供回答时，人格画像分数会根据回答进行修正。
5. 提供当前持仓时，生成非空 `suitability`。
6. 报告 Markdown 包含免责声明，且不包含具体买卖建议。
7. 完整分析结果包含 `llm_enrichment.status=FALLBACK`。
