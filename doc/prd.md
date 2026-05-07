# PRD：AI 投资人格与持仓适配分析系统

版本：v0.1  
状态：MVP PRD  
目标文件：`prd.md`  
产品定位：交割单驱动的投资行为画像与持仓适配分析系统  
重要边界：本系统不提供具体股票买入、卖出、调仓建议，不承诺收益，不构成投资建议。系统仅用于风险画像、行为偏差识别、持仓适配度分析与投资者教育。

---

## 1. 背景与问题定义

### 1.1 背景

传统投资风险测评主要依赖问卷，例如：

- 你能承受多大亏损？
- 你偏好稳健还是激进？
- 你是否会长期持有？
- 你是否理解股票风险？

但这类问卷存在明显问题：

1. 用户容易回答成“理想中的自己”，而不是“真实交易中的自己”。
2. 用户可能回避自身问题，例如追涨、杀跌、补仓失控、频繁交易。
3. 问卷缺少真实行为证据，难以判断回答可信度。
4. 不同用户面临的问题不同，统一问卷无法精准触达关键行为。
5. 投资者真实风险并不只来自持仓本身，也来自其在压力场景下的交易行为。

因此，本产品采用“交割单驱动”的方式：

> 先从用户真实交易记录中识别代表性行为片段，再基于这些片段向用户提出高相关度问题，最终生成投资人格画像，并判断当前持仓是否与其人格、行为习惯和风险承受能力匹配。

---

## 2. 产品目标

### 2.1 核心目标

构建一个能够基于用户交割单和当前持仓，完成以下任务的系统：

1. 解析用户交割单。
2. 识别用户真实交易行为模式。
3. 找出最具代表性的 3-5 个行为片段。
4. 基于行为片段生成针对性追问。
5. 结合行为证据与用户回答生成投资人格画像。
6. 判断当前持仓是否有利于该用户的性格、行为模式和风险承受能力。
7. 输出可解释、可复盘、可行动的风险分析报告。

### 2.2 用户价值

对股民：

- 了解自己真实交易行为，而不是主观想象。
- 识别亏损背后的行为偏差。
- 判断当前持仓是否适合自己的性格和承受能力。
- 获得更有针对性的风险提示。

对产品方：

- 提供差异化投资者画像能力。
- 避免直接荐股带来的合规风险。
- 通过用户真实数据生成高粘性的分析报告。
- 为后续投教、组合体检、风控提醒、用户分层打基础。

---

## 3. 产品定位与边界

### 3.1 产品定位

产品名称建议：

> AI 投资人格与持仓适配分析系统

一句话说明：

> 通过用户真实交割单识别投资行为模式，分析其投资人格，并判断当前持仓是否与其性格、风险承受能力和交易习惯匹配。

### 3.2 本产品可以做

- 交割单解析
- 交易行为识别
- 代表性行为片段提取
- 个性化问题生成
- 投资人格画像
- 风险承受匹配分析
- 当前持仓适配度分析
- 行为偏差提醒
- 仓位集中度提示
- 交易复盘建议
- 投资者教育内容推荐

### 3.3 本产品不做

- 不推荐具体股票
- 不给出明确买入、卖出、加仓、减仓指令
- 不预测个股收益
- 不承诺收益或回撤控制
- 不代替持牌投资顾问
- 不自动交易
- 不基于人格标签直接判断某只股票一定适合或不适合

### 3.4 合规表达边界

可以表达：

> 当前组合波动特征与用户损失厌恶倾向存在不匹配，若市场下跌，用户可能出现情绪性卖出风险。

不应表达：

> 你应该卖出 A 股票。

可以表达：

> 当前单一股票仓位较高，结合用户历史补仓行为，存在集中度风险和回撤压力。

不应表达：

> A 股票不适合你，建议换成 B 股票。

---

## 4. 目标用户

### 4.1 C 端用户

| 用户类型 | 特征 | 需求 |
|---|---|---|
| 新手股民 | 交易经验少，容易跟风 | 了解自己是否在追涨杀跌 |
| 亏损股民 | 有历史亏损，想复盘 | 找到亏损背后的行为问题 |
| 高频交易者 | 交易频繁，换手率高 | 判断是否存在冲动交易 |
| 长期投资者 | 自认为价值投资 | 验证行为是否真的长期稳定 |
| 重仓投资者 | 单票或行业集中 | 判断集中度是否超出性格承受 |
| 情绪型投资者 | 容易焦虑、后悔、踏空 | 识别情绪对交易的影响 |

---

## 5. MVP 范围

### 5.1 MVP 必须支持

1. 用户上传交割单。
2. 系统解析交易记录。
3. 系统按股票切分持仓周期。
4. 系统识别至少 6 类行为片段：
   - 亏损补仓
   - 追涨买入
   - 杀跌卖出
   - 盈利早卖 / 亏损久拿
   - 卖出后追回
   - 单票重仓
5. 系统从候选行为片段中选出 3-5 个代表性片段。
6. 系统针对每个片段生成 2-3 个问题。
7. 用户回答问题。
8. 系统生成投资人格画像。
9. 系统分析当前持仓与人格的适配度。
10. 系统生成一份结构化报告。

### 5.2 MVP 暂不支持

- 自动读取券商账户
- 自动交易
- 个股推荐
- 复杂衍生品分析
- 融资融券精细化风控
- 跨账户合并分析
- 实时行情监控
- AI 自主调仓
- 完整税务分析

---

## 6. 核心用户流程

### 6.1 主流程

```text
用户上传交割单
    ↓
系统解析与字段映射
    ↓
用户确认解析结果
    ↓
系统生成持仓周期
    ↓
系统识别候选行为片段
    ↓
系统选择最具代表性的 3-5 个片段
    ↓
系统生成针对性问题
    ↓
用户回答问题
    ↓
系统生成投资人格画像
    ↓
用户上传或确认当前持仓
    ↓
系统分析当前持仓适配度
    ↓
生成完整报告
```

### 6.2 关键体验原则

1. 不先问抽象性格问题。
2. 先展示真实交易观察。
3. 每个问题必须绑定一个行为证据。
4. 问题必须追问“当时为什么”，而不是问“你是不是”。
5. 输出结论必须体现不确定性，避免绝对判断。
6. 系统要区分“理性策略”和“行为偏差”。

---

## 7. 数据输入

### 7.1 交割单输入

MVP 支持格式：

| 格式 | 是否支持 | 说明 |
|---|---|---|
| CSV | 必须支持 | 优先支持 |
| Excel | 必须支持 | `.xls` / `.xlsx` |
| PDF | 可选支持 | MVP 可后置 |
| 图片截图 | 暂不支持 | 后续可 OCR |
| 券商 API | 暂不支持 | 后续版本 |

### 7.2 交割单标准字段

系统需要将不同券商格式统一映射为以下字段。

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | string | 是 | 用户 ID |
| account_id | string | 是 | 账户 ID |
| trade_id | string | 否 | 成交编号，没有则系统生成 |
| trade_date | datetime | 是 | 成交时间 |
| settlement_date | date | 否 | 交割日期 |
| symbol | string | 是 | 股票代码 |
| stock_name | string | 否 | 股票名称 |
| exchange | string | 否 | 交易所 |
| side | enum | 是 | BUY / SELL |
| quantity | number | 是 | 成交数量 |
| price | number | 是 | 成交价格 |
| gross_amount | number | 是 | 成交金额 |
| fee | number | 否 | 手续费 |
| tax | number | 否 | 印花税等 |
| net_amount | number | 否 | 净成交金额 |
| currency | string | 否 | 币种 |
| trade_type | string | 否 | 普通买卖、分红、配股、新股中签等 |
| source_file_id | string | 是 | 来源文件 ID |

### 7.3 当前持仓输入

| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| snapshot_date | date | 是 | 持仓日期 |
| user_id | string | 是 | 用户 ID |
| account_id | string | 是 | 账户 ID |
| symbol | string | 是 | 股票代码 |
| stock_name | string | 否 | 股票名称 |
| quantity | number | 是 | 当前持仓数量 |
| market_price | number | 是 | 当前价格 |
| market_value | number | 是 | 当前市值 |
| cost_basis | number | 否 | 持仓成本 |
| unrealized_pnl | number | 否 | 未实现盈亏 |
| unrealized_pnl_pct | number | 否 | 未实现盈亏比例 |
| position_weight | number | 是 | 持仓占总资产比例 |
| sector | string | 否 | 行业 |
| currency | string | 否 | 币种 |

### 7.4 市场数据输入

用于判断追涨、杀跌、波动率、回撤、行业等。

| 字段 | 说明 |
|---|---|
| symbol | 股票代码 |
| date | 交易日 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| adjusted_close | 复权收盘价 |
| sector | 行业 |
| market_cap | 市值 |
| benchmark_return | 基准收益 |
| volatility_20d | 20 日波动率 |
| volatility_60d | 60 日波动率 |
| max_drawdown_60d | 60 日最大回撤 |

---

## 8. 数据清洗与标准化

### 8.1 清洗目标

将不同券商、不同格式、不同字段名称的交割单转换为标准交易表 `normalized_trades`。

### 8.2 字段映射规则

系统需要支持常见字段别名。

| 标准字段 | 可能出现的字段名 |
|---|---|
| trade_date | 成交日期、交易日期、成交时间、日期 |
| symbol | 证券代码、股票代码、标的代码 |
| stock_name | 证券名称、股票名称、标的名称 |
| side | 买卖方向、操作、业务名称 |
| quantity | 成交数量、数量、发生数量 |
| price | 成交价格、价格、成交均价 |
| gross_amount | 成交金额、发生金额、金额 |
| fee | 手续费、佣金、费用 |
| tax | 印花税、税费 |

### 8.3 买卖方向标准化

| 原始值 | 标准值 |
|---|---|
| 买入 | BUY |
| 证券买入 | BUY |
| B | BUY |
| 卖出 | SELL |
| 证券卖出 | SELL |
| S | SELL |

### 8.4 非主动交易过滤

以下交易类型默认不参与行为偏差识别，但可以保留在原始数据中：

- 分红入账
- 股息红利
- 配股
- 送股
- 转托管
- 新股中签
- 债券兑付
- 基金分红
- 系统调账

处理规则：

```text
if trade_type in 非主动交易类型:
    active_trade = false
else:
    active_trade = true
```

只有 `active_trade = true` 的记录进入行为片段识别。

### 8.5 数据校验

| 校验项 | 规则 | 失败处理 |
|---|---|---|
| 日期为空 | trade_date 必须存在 | 阻断 |
| 代码为空 | symbol 必须存在 | 阻断 |
| 数量异常 | quantity > 0 | 阻断 |
| 价格异常 | price > 0 | 阻断 |
| 金额异常 | gross_amount >= 0 | 警告 |
| 买卖方向无法识别 | side 必须为 BUY/SELL | 要求用户映射 |
| 重复成交 | 同日期、同代码、同方向、同数量、同价格 | 合并或提示 |
| 时间范围太短 | 少于 20 个交易日 | 提示分析可信度低 |
| 交易笔数太少 | 少于 10 笔主动交易 | 提示样本不足 |

---

## 9. 持仓周期构建

### 9.1 定义

持仓周期是指同一只股票从持仓为 0 到再次归 0 的完整过程。

```text
当某股票持仓从 0 变为 >0：开启一个持仓周期
当某股票持仓从 >0 变为 0：结束一个持仓周期
如果到当前仍未清仓：周期结束日 = 当前日期，status = OPEN
```

### 9.2 持仓周期字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| cycle_id | string | 持仓周期 ID |
| user_id | string | 用户 ID |
| account_id | string | 账户 ID |
| symbol | string | 股票代码 |
| stock_name | string | 股票名称 |
| start_date | date | 首次建仓日期 |
| end_date | date | 清仓日期或当前日期 |
| status | enum | OPEN / CLOSED |
| trade_count | number | 周期内交易笔数 |
| buy_count | number | 买入次数 |
| sell_count | number | 卖出次数 |
| first_buy_price | number | 首次买入价格 |
| avg_buy_price | number | 加权平均买入价格 |
| avg_sell_price | number | 加权平均卖出价格 |
| max_position_quantity | number | 最大持仓数量 |
| max_position_value | number | 最大持仓市值 |
| max_position_weight | number | 最大仓位占比 |
| realized_pnl | number | 已实现盈亏 |
| realized_pnl_pct | number | 已实现盈亏比例 |
| unrealized_pnl | number | 未实现盈亏 |
| max_drawdown_pct | number | 周期内最大浮亏 |
| max_profit_pct | number | 周期内最大浮盈 |
| hold_days | number | 持仓天数 |
| is_current_holding | boolean | 是否当前仍持有 |

### 9.3 持仓周期算法伪代码

```python
def build_position_cycles(trades):
    cycles = []
    current_cycles = {}

    trades = sort_by_user_account_symbol_date(trades)

    for trade in trades:
        key = (trade.user_id, trade.account_id, trade.symbol)

        if key not in current_cycles:
            current_cycles[key] = None

        cycle = current_cycles[key]

        if cycle is None and trade.side == "BUY":
            cycle = create_new_cycle(trade)
            current_cycles[key] = cycle

        if cycle is not None:
            cycle.add_trade(trade)
            cycle.update_position(trade)

            if cycle.position_quantity == 0:
                cycle.close(end_date=trade.trade_date)
                cycles.append(cycle)
                current_cycles[key] = None

    for cycle in current_cycles.values():
        if cycle is not None:
            cycle.mark_open(end_date=today())
            cycles.append(cycle)

    return cycles
```

### 9.4 成本计算规则

MVP 使用移动加权成本法。

```text
买入后平均成本 =
(原持仓成本金额 + 本次买入金额 + 本次费用) / 新持仓数量
```

卖出时实现盈亏：

```text
卖出实现盈亏 =
卖出数量 × (卖出价格 - 当前平均成本) - 卖出费用 - 税费
```

### 9.5 仓位占比计算

若用户提供每日账户总资产：

```text
position_weight = 股票市值 / 当日账户总资产
```

若用户没有提供账户总资产：

```text
账户总资产估算 = 当前持仓市值 + 可识别现金余额
```

若现金余额不可得：

```text
使用上传交割单期间出现过的最大持仓市值总和作为近似账户规模
```

可信度标记：

| 情况 | 可信度 |
|---|---|
| 用户提供每日账户资产 | HIGH |
| 用户提供当前总资产 | MEDIUM |
| 系统估算账户资产 | LOW |

---

## 10. 行为片段识别

行为片段不是单笔成交，而是一段具有心理解释价值的交易故事。

每个行为片段必须包含：

1. 行为类型
2. 发生时间
3. 涉及股票
4. 关键交易序列
5. 资金影响
6. 盈亏影响
7. 可解释的心理假设
8. 后续可追问的问题主题

---

# 10.1 行为类型一：亏损补仓

## 定义

用户在同一股票处于浮亏状态时继续买入，导致仓位扩大。

## 触发条件

满足以下条件即生成候选片段：

```text
同一持仓周期内：
1. 首次买入后价格下跌；
2. 后续至少 1 次买入发生在浮亏状态；
3. 补仓后持仓数量或市值增加；
4. 该片段最大仓位占比 >= 5%，或补仓金额 >= 账户估算资产 5%。
```

强触发条件：

```text
亏损补仓次数 >= 2
且最大浮亏 <= -10%
且最大仓位占比 >= 10%
```

## 关键指标

| 指标 | 说明 |
|---|---|
| avg_down_count | 浮亏状态下买入次数 |
| first_loss_buy_drawdown | 第一次亏损补仓时浮亏 |
| max_drawdown_pct | 周期最大浮亏 |
| position_increase_ratio | 补仓后仓位扩大倍数 |
| max_position_weight | 最大单票仓位 |
| final_pnl_pct | 最终盈亏 |
| is_current_holding | 是否当前仍持有 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    avg_down_count * 20
    + abs(max_drawdown_pct) * 100 * 0.8
    + position_increase_ratio * 15
)
```

示例：

| 情况 | 强度 |
|---|---|
| 亏损补仓 1 次，最大浮亏 5% | 低 |
| 亏损补仓 2 次，最大浮亏 12% | 中 |
| 亏损补仓 3 次以上，最大浮亏 20%+ | 高 |

## 可解释心理假设

可能反映：

- 回本心理
- 沉没成本偏误
- 不愿承认错误
- 价值投资式分批买入
- 缺乏止损规则
- 仓位管理失控

注意：系统不得直接判定用户一定是赌徒心态，必须通过追问区分。

## 问题主题

- 当时补仓是否有计划？
- 补仓依据是估值、基本面还是回本心理？
- 是否有最大仓位上限？
- 是否有退出机制？

---

# 10.2 行为类型二：追涨买入

## 定义

用户在股票短期已经明显上涨后买入，可能存在 FOMO、从众或趋势确认行为。

## 触发条件

```text
买入日前 5 个交易日涨幅 >= 8%
或买入日前 10 个交易日涨幅 >= 15%
且本次买入金额占账户资产 >= 3%
```

强触发条件：

```text
买入日前 10 个交易日涨幅 >= 25%
且买入后 10 个交易日收益 <= -5%
或买入后 20 个交易日内卖出
```

## 关键指标

| 指标 | 说明 |
|---|---|
| pre_buy_return_3d | 买入前 3 日涨幅 |
| pre_buy_return_5d | 买入前 5 日涨幅 |
| pre_buy_return_10d | 买入前 10 日涨幅 |
| buy_amount_ratio | 买入金额占账户比例 |
| post_buy_return_5d | 买入后 5 日收益 |
| post_buy_return_10d | 买入后 10 日收益 |
| sell_within_20d | 是否 20 日内卖出 |
| sector_hotness_score | 板块热度分 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    pre_buy_return_5d * 100 * 2
    + pre_buy_return_10d * 100
    + buy_amount_ratio * 100 * 1.5
    + short_term_loss_bonus
)
```

其中：

```text
if post_buy_return_10d <= -0.05:
    short_term_loss_bonus = 15
else:
    short_term_loss_bonus = 0
```

## 可解释心理假设

可能反映：

- 害怕错过机会
- 热点追逐
- 从众行为
- 短线趋势策略
- 信息来源受市场情绪影响
- 缺乏买入前计划

## 问题主题

- 买入前是否已有研究？
- 是趋势确认还是怕错过？
- 信息来源是什么？
- 是否设置买入后退出规则？

---

# 10.3 行为类型三：杀跌卖出

## 定义

用户在短期亏损后快速卖出，且卖出后股票出现反弹，可能存在情绪性止损或恐慌卖出。

## 触发条件

```text
买入后 20 个交易日内卖出
且卖出时收益 <= -5%
```

强化条件：

```text
卖出后 20 个交易日内股价反弹 >= 8%
```

## 关键指标

| 指标 | 说明 |
|---|---|
| loss_at_sell_pct | 卖出时亏损比例 |
| hold_days | 持仓天数 |
| sell_ratio | 卖出比例 |
| rebound_after_sell_5d | 卖出后 5 日反弹 |
| rebound_after_sell_20d | 卖出后 20 日反弹 |
| was_stop_loss_planned | 是否有计划止损，来自用户回答 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    abs(loss_at_sell_pct) * 100 * 2
    + max(0, 20 - hold_days) * 2
    + rebound_after_sell_20d * 100
)
```

## 可解释心理假设

可能反映：

- 损失厌恶
- 情绪敏感
- 恐慌卖出
- 有纪律的止损
- 买入逻辑不稳定
- 缺少持仓预案

## 问题主题

- 卖出是否触发事先止损？
- 是否因害怕继续亏损而卖？
- 卖出后是否复盘？
- 下次遇到类似情况是否有规则？

---

# 10.4 行为类型四：盈利早卖 / 亏损久拿

## 定义

用户倾向于快速卖出盈利股票，却长期持有亏损股票，可能存在处置效应。

## 触发条件

需要在用户层面统计，而不是单一持仓周期。

```text
盈利闭环交易数量 >= 3
亏损闭环交易数量 >= 3
且亏损交易平均持仓天数 / 盈利交易平均持仓天数 >= 2
```

或：

```text
小盈利卖出比例 >= 50%
且长期亏损持有比例 >= 30%
```

定义：

```text
小盈利卖出：0 < realized_pnl_pct <= 5%
长期亏损持有：hold_days >= 60 且期间 max_drawdown_pct <= -10%
```

## 关键指标

| 指标 | 说明 |
|---|---|
| avg_win_hold_days | 盈利交易平均持仓天数 |
| avg_loss_hold_days | 亏损交易平均持仓天数 |
| win_loss_hold_ratio | 亏损持有天数 / 盈利持有天数 |
| small_profit_sell_ratio | 小盈利卖出比例 |
| long_loss_hold_ratio | 长期亏损持有比例 |
| disposition_score | 处置效应分 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    win_loss_hold_ratio * 20
    + small_profit_sell_ratio * 100 * 0.4
    + long_loss_hold_ratio * 100 * 0.4
)
```

## 可解释心理假设

可能反映：

- 落袋为安
- 害怕利润回吐
- 不愿面对亏损
- 回避亏损确认
- 缺乏止盈止损体系
- 长期投资但缺少再评估机制

## 问题主题

- 为什么盈利较小时卖出？
- 为什么亏损较大时继续持有？
- 是否有统一的退出规则？
- 是否区分价值持有和被动套牢？

---

# 10.5 行为类型五：卖出后追回

## 定义

用户卖出某股票后，在较短时间内又买回，尤其是买回价格高于卖出价格，可能反映后悔、踏空焦虑或策略不稳定。

## 触发条件

```text
同一股票卖出后 20 个交易日内重新买入
且买回价格 >= 卖出价格 * 1.03
```

或：

```text
同一股票 60 日内发生 2 次以上卖出后买回
```

## 关键指标

| 指标 | 说明 |
|---|---|
| repurchase_days | 卖出后几天买回 |
| buyback_price_gap_pct | 买回价相对卖出价变化 |
| round_trip_count | 往返次数 |
| total_fees | 交易成本 |
| post_sell_return_before_buyback | 卖出后到买回前涨幅 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    (20 - repurchase_days) * 2
    + buyback_price_gap_pct * 100 * 2
    + round_trip_count * 15
)
```

## 可解释心理假设

可能反映：

- 后悔厌恶
- 害怕踏空
- 策略摇摆
- 交易纪律不足
- 短线策略执行
- 新信息改变判断

## 问题主题

- 重新买入是因为新信息还是后悔？
- 是否存在明确交易计划？
- 卖出前是否知道重新买入条件？
- 是否经常因价格上涨而改变判断？

---

# 10.6 行为类型六：单票重仓

## 定义

用户在单只股票上投入过高仓位，可能带来集中度风险。

## 触发条件

```text
单只股票最大仓位 >= 20%
```

强触发：

```text
单只股票最大仓位 >= 35%
```

如果用户为新手或历史显示损失厌恶较高，可降低阈值：

```text
单只股票最大仓位 >= 15%
```

## 关键指标

| 指标 | 说明 |
|---|---|
| max_position_weight | 最大仓位占比 |
| concentration_days | 重仓持续天数 |
| pnl_impact_pct | 对账户整体盈亏影响 |
| concentration_source | 主动重仓 / 补仓导致 / 上涨导致 |
| sector_overlap | 是否与其他持仓同属高相关行业 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    max_position_weight * 100 * 2
    + min(concentration_days, 120) * 0.2
    + abs(pnl_impact_pct) * 100
)
```

## 可解释心理假设

可能反映：

- 高确定性信念
- 过度自信
- 仓位管理不足
- 补仓导致被动重仓
- 风险集中但未感知
- 价值投资集中持仓

## 问题主题

- 是否意识到该仓位比例？
- 是否有单票仓位上限？
- 重仓基于研究还是情绪？
- 如果下跌 20%，是否能承受？

---

# 10.7 行为类型七：频繁交易 / 策略漂移

## 定义

用户在较短时间内频繁买卖，平均持仓时间短，可能存在冲动交易或策略不稳定。

## 触发条件

```text
月换手率 >= 200%
或平均持仓周期 <= 10 个交易日
或 30 日内主动交易笔数 >= 20
```

## 关键指标

| 指标 | 说明 |
|---|---|
| monthly_turnover | 月换手率 |
| avg_hold_days | 平均持仓天数 |
| active_trade_count_30d | 30 日主动交易次数 |
| repeated_symbol_ratio | 重复交易同一股票比例 |
| fee_drag_pct | 手续费对收益拖累 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    monthly_turnover * 20
    + max(0, 20 - avg_hold_days) * 3
    + active_trade_count_30d
)
```

## 可解释心理假设

可能反映：

- 冲动交易
- 机会焦虑
- 缺乏耐心
- 短线策略
- 高频复盘能力
- 执行纪律不足

## 问题主题

- 是否本来就是短线策略？
- 每次买卖是否有明确触发条件？
- 是否统计过交易成本？
- 是否经常临时改变计划？

---

# 10.8 行为类型八：热点切换

## 定义

用户频繁买入近期热门行业或主题，持仓行业变化快。

## 触发条件

```text
60 日内涉及行业数量 >= 5
且买入行业中，超过 50% 属于当期高热度行业
```

行业热度可通过以下方式估算：

```text
sector_hotness_score =
行业近 20 日收益排名分
+ 行业成交额放大分
+ 行业新闻热度分
```

MVP 可先仅用行业近 20 日收益排名。

## 关键指标

| 指标 | 说明 |
|---|---|
| sector_count_60d | 60 日交易行业数量 |
| hot_sector_buy_ratio | 热门行业买入比例 |
| avg_sector_hold_days | 行业平均持有天数 |
| sector_switch_count | 行业切换次数 |
| post_hot_buy_return | 买入热点后收益 |

## 行为强度评分

```text
behavior_intensity =
min(100,
    sector_count_60d * 8
    + hot_sector_buy_ratio * 100 * 0.5
    + sector_switch_count * 5
)
```

## 可解释心理假设

可能反映：

- 从众
- 热点依赖
- 信息噪音驱动
- 缺乏长期主线
- 板块轮动策略
- 追逐短期收益

## 问题主题

- 信息来源是什么？
- 是否理解行业逻辑？
- 是主动轮动策略还是看到热点后买入？
- 是否有退出标准？

---

## 11. 代表性行为片段选择器

模块名称：

```text
Representative Behavior Segment Selector
```

中文名称：

```text
代表性行为片段选择器
```

### 11.1 输入

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "normalized_trades": [],
  "position_cycles": [],
  "current_holdings": [],
  "market_data": [],
  "account_asset_series": []
}
```

### 11.2 输出

```json
{
  "user_id": "U001",
  "selected_segments": [
    {
      "segment_id": "SEG_001",
      "behavior_type": "LOSS_AVERAGING_DOWN",
      "stock_code": "600000",
      "stock_name": "示例股票",
      "start_date": "2025-03-01",
      "end_date": "2025-04-15",
      "summary": "用户在股价下跌过程中连续补仓 3 次，仓位从 8% 提升至 31%。",
      "evidence": {},
      "scores": {},
      "question_themes": []
    }
  ]
}
```

### 11.3 候选片段生成流程

```text
1. 遍历所有持仓周期。
2. 对每个持仓周期执行 8 类行为检测器。
3. 每个检测器返回 0 个或多个候选片段。
4. 合并用户层面的行为片段，例如处置效应、频繁交易、热点切换。
5. 对所有候选片段计算代表性分数。
6. 过滤噪音片段。
7. 执行多样性选择。
8. 输出 3-5 个片段。
```

### 11.4 代表性总分公式

```text
segment_score =
behavior_intensity_score * 0.30
+ capital_impact_score * 0.25
+ emotion_signal_score * 0.20
+ recency_score * 0.10
+ current_position_score * 0.10
+ explainability_score * 0.05
- noise_penalty
```

### 11.5 分项说明

#### 11.5.1 行为强度分

范围：0-100  
说明：该行为是否明显。

示例：

| 行为 | 低分 | 高分 |
|---|---|---|
| 亏损补仓 | 补仓 1 次，小浮亏 | 补仓 3 次以上，大浮亏 |
| 追涨 | 买入前涨 5% | 买入前涨 25% |
| 杀跌 | 亏损 3% 卖出 | 亏损 15% 快速卖出 |
| 重仓 | 单票 12% | 单票 40% |
| 追回 | 卖出后 30 天买回 | 卖出后 3 天高价买回 |

#### 11.5.2 资金影响分

范围：0-100

```text
capital_impact_score = min(100, max_capital_used_ratio * 100 * 2.5)
```

示例：

| 最大占用账户资金 | 分数 |
|---|---:|
| 3% | 7.5 |
| 10% | 25 |
| 20% | 50 |
| 30% | 75 |
| 40%+ | 100 |

#### 11.5.3 情绪信号分

范围：0-100  
说明：该行为是否有较强心理解释价值。

初始默认分：

| 行为类型 | 默认情绪信号分 |
|---|---:|
| 亏损补仓 | 85 |
| 卖出后追回 | 85 |
| 盈利早卖 / 亏损久拿 | 80 |
| 杀跌卖出 | 75 |
| 追涨买入 | 75 |
| 单票重仓 | 70 |
| 频繁交易 | 70 |
| 热点切换 | 65 |

可根据是否有计划性证据调整：

```text
如果用户回答显示事前有明确计划：emotion_signal_score - 20
如果行为反复出现：emotion_signal_score + 10
如果金额很小：emotion_signal_score - 15
```

#### 11.5.4 近期相关分

范围：0-100

```text
days_ago = 当前日期 - 片段结束日期
```

| 时间 | 分数 |
|---|---:|
| 30 天内 | 100 |
| 90 天内 | 80 |
| 180 天内 | 60 |
| 365 天内 | 40 |
| 365 天以前 | 20 |

#### 11.5.5 当前持仓相关分

范围：0-100

| 情况 | 分数 |
|---|---:|
| 片段股票当前仍持有 | 100 |
| 片段股票已清仓但同类行为影响当前持仓 | 70 |
| 片段与当前持仓同行业 | 50 |
| 历史片段，与当前无明显关系 | 20 |

#### 11.5.6 可解释性分

范围：0-100

| 情况 | 分数 |
|---|---:|
| 证据完整，容易生成问题 | 100 |
| 证据较完整，但缺少部分行情 | 70 |
| 只有交易数据，缺少持仓/行情 | 50 |
| 数据不完整，不适合追问 | 20 |

#### 11.5.7 噪音惩罚

| 噪音类型 | 扣分 |
|---|---:|
| 金额低于账户 1% | -30 |
| 非主动交易 | -50 |
| 数据缺失严重 | -30 |
| 疑似新股中签 / 分红 / 配股 | -40 |
| 持仓周期少于 1 天且金额小 | -20 |
| 与其他高分片段完全重复 | -20 |
| 股票停牌或异常价格导致误判 | -20 |

### 11.6 过滤规则

候选片段需要满足：

```text
segment_score >= 60
capital_impact_score >= 10
explainability_score >= 50
noise_penalty > -50
```

如果用户交易样本不足：

```text
segment_score >= 50
```

并在报告中标记：

```text
分析可信度：低，原因：交易样本不足
```

### 11.7 多样性选择规则

目标：选出 3-5 个最能覆盖不同心理维度的片段。

规则：

```text
1. 最多选择 5 个片段。
2. 最少选择 3 个片段；如果候选不足 3 个，则选择全部并标记样本不足。
3. 同一行为类型最多 2 个。
4. 同一股票最多 1 个，除非该股票当前仍持有且风险极高。
5. 当前持仓相关片段至少 1 个，如存在。
6. 最大资金影响片段至少 1 个。
7. 高情绪信号片段至少 1 个。
8. 优先覆盖不同心理维度。
```

### 11.8 心理维度覆盖映射

| 行为类型 | 心理维度 |
|---|---|
| 亏损补仓 | 回本心理、沉没成本、风险承受 |
| 追涨买入 | FOMO、从众、信息来源 |
| 杀跌卖出 | 损失厌恶、情绪稳定性 |
| 盈利早卖 / 亏损久拿 | 处置效应、亏损回避 |
| 卖出后追回 | 后悔厌恶、踏空焦虑 |
| 单票重仓 | 过度自信、集中度容忍 |
| 频繁交易 | 冲动性、耐心、策略稳定 |
| 热点切换 | 从众、信息噪音、主线缺失 |

### 11.9 多样性选择伪代码

```python
def select_representative_segments(candidates, max_segments=5):
    candidates = sorted(candidates, key=lambda x: x.segment_score, reverse=True)

    selected = []
    behavior_type_count = {}
    selected_symbols = set()
    covered_dimensions = set()

    # 1. 先确保当前持仓相关片段
    current_related = [
        c for c in candidates
        if c.current_position_score >= 70
    ]
    if current_related:
        best = current_related[0]
        selected.append(best)
        update_state(best)

    # 2. 确保最大资金影响片段
    capital_sorted = sorted(
        candidates,
        key=lambda x: x.capital_impact_score,
        reverse=True
    )
    for c in capital_sorted:
        if can_add(c, selected, behavior_type_count, selected_symbols):
            selected.append(c)
            update_state(c)
            break

    # 3. 按总分与维度增益选择
    for c in candidates:
        if len(selected) >= max_segments:
            break

        if not can_add(c, selected, behavior_type_count, selected_symbols):
            continue

        dimension_gain = count_new_dimensions(c.dimensions, covered_dimensions)

        if dimension_gain > 0 or c.segment_score >= 85:
            selected.append(c)
            update_state(c)

    # 4. 如果不足 3 个，放宽去重条件补齐
    if len(selected) < 3:
        for c in candidates:
            if c not in selected:
                selected.append(c)
            if len(selected) >= 3:
                break

    return selected[:max_segments]
```

---

## 12. 行为片段数据结构

### 12.1 标准 JSON

```json
{
  "segment_id": "SEG_001",
  "user_id": "U001",
  "account_id": "A001",
  "behavior_type": "LOSS_AVERAGING_DOWN",
  "behavior_name": "亏损补仓",
  "symbol": "600000",
  "stock_name": "示例股票",
  "start_date": "2025-03-01",
  "end_date": "2025-04-15",
  "status": "OPEN",
  "summary": "用户在股价下跌过程中连续补仓 3 次，仓位从 8% 提升至 31%，期间最大浮亏 22%。",
  "evidence": {
    "avg_down_count": 3,
    "max_position_weight": 0.31,
    "max_drawdown_pct": -0.22,
    "position_increase_ratio": 3.8,
    "realized_pnl_pct": null,
    "unrealized_pnl_pct": -0.18,
    "hold_days": 45,
    "is_current_holding": true
  },
  "scores": {
    "behavior_intensity_score": 88,
    "capital_impact_score": 78,
    "emotion_signal_score": 85,
    "recency_score": 90,
    "current_position_score": 100,
    "explainability_score": 95,
    "noise_penalty": 0,
    "segment_score": 87
  },
  "psychological_hypotheses": [
    "回本心理",
    "沉没成本偏误",
    "价值投资式分批买入",
    "仓位管理风险"
  ],
  "question_themes": [
    "补仓动机",
    "最大仓位意识",
    "退出机制",
    "风险承受能力"
  ],
  "confidence": "HIGH"
}
```

### 12.2 置信度规则

| 置信度 | 条件 |
|---|---|
| HIGH | 交易数据、行情数据、账户资产数据完整 |
| MEDIUM | 缺少账户资产，但交易和行情完整 |
| LOW | 缺少行情或账户资产，只能基于交易推断 |

---

## 13. 问题生成引擎

模块名称：

```text
Behavior-Based Question Engine
```

中文名称：

```text
基于行为片段的问题生成引擎
```

### 13.1 设计原则

1. 每个问题必须绑定一个真实行为片段。
2. 不问“你是不是容易追涨”，而问“当时为什么买入”。
3. 问题要包含事实观察、动机追问和事后复盘。
4. 选项必须能区分理性策略与行为偏差。
5. 用户应能否认系统观察，但否认本身也可作为可信度信息。
6. 每个片段默认生成 3 道题。
7. MVP 总问题数控制在 9-15 题。

### 13.2 每个片段的问题结构

```text
问题 1：事实确认
问题 2：交易动机
问题 3：事后复盘 / 风险预案
```

### 13.3 事实确认题模板

```text
系统观察到：
你在 {stock_name} 上出现了 {behavior_summary}。

这个描述是否符合你当时的交易情况？

A. 完全符合
B. 基本符合
C. 不太符合
D. 不记得
```

评分：

| 选项 | 含义 | 分数影响 |
|---|---|---|
| A | 接受行为证据 | observation_confidence +20 |
| B | 基本接受 | observation_confidence +10 |
| C | 否认 | observation_confidence -20 |
| D | 不确定 | observation_confidence -10 |

### 13.4 动机追问题模板：亏损补仓

```text
当时你在 {stock_name} 下跌后继续加仓，主要原因更接近哪一种？

A. 我重新评估后认为公司价值更有吸引力
B. 我原本就计划分批建仓，并有明确仓位上限
C. 我主要想降低持仓成本，等待反弹回本
D. 我不愿意承认前面买错了
E. 当时没有明确计划，只是觉得跌多了会涨
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 研究驱动 +15，纪律性 +5 |
| B | 计划性 +20，仓位意识 +15 |
| C | 回本心理 +20，损失厌恶 +10 |
| D | 沉没成本 +20，自我修正 -10 |
| E | 冲动性 +15，纪律性 -15 |

### 13.5 动机追问题模板：追涨买入

```text
你在买入 {stock_name} 前，该股票短期已经明显上涨。你当时买入的主要原因是什么？

A. 我已长期跟踪，认为上涨验证了我的判断
B. 技术趋势突破，符合我的交易系统
C. 看到股价持续上涨，担心错过机会
D. 看到新闻、群聊、短视频或朋友推荐
E. 没有明确理由，只是感觉还会继续涨
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 研究驱动 +15，FOMO -5 |
| B | 策略纪律 +15 |
| C | FOMO +20 |
| D | 从众 +20，信息质量风险 +15 |
| E | 冲动性 +20，策略稳定性 -15 |

### 13.6 动机追问题模板：杀跌卖出

```text
你在 {stock_name} 出现亏损后较快卖出。卖出时更接近下面哪种情况？

A. 到达了事先设定的止损线
B. 基本面或买入逻辑发生了变化
C. 担心继续亏损，想先退出
D. 看到市场情绪变差或别人也在卖
E. 当时没有计划，只是不想再看到账户亏损
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 纪律性 +20 |
| B | 研究驱动 +15 |
| C | 损失厌恶 +20 |
| D | 从众 +15，情绪敏感 +10 |
| E | 情绪交易 +20，计划性 -15 |

### 13.7 动机追问题模板：盈利早卖 / 亏损久拿

```text
系统发现你在部分交易中盈利较小时就卖出，但亏损股票持有时间更长。你卖出盈利股票时最常见的原因是什么？

A. 达到事先设定的止盈目标
B. 基本面或价格逻辑已经变化
C. 觉得先落袋为安
D. 害怕利润回吐
E. 没有固定规则，看到赚钱就想卖
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 纪律性 +20 |
| B | 研究驱动 +15 |
| C | 处置效应 +15 |
| D | 利润回吐焦虑 +20 |
| E | 策略稳定性 -15，情绪交易 +15 |

### 13.8 动机追问题模板：卖出后追回

```text
你曾经卖出 {stock_name} 后又在较短时间内重新买回。重新买入时的主要原因是什么？

A. 出现了新的重要信息，改变了判断
B. 价格重新触发了我的交易系统
C. 卖出后上涨，担心踏空
D. 后悔之前卖早了
E. 没有明确原因，只是又觉得它会涨
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 信息更新能力 +10 |
| B | 策略纪律 +20 |
| C | FOMO +20 |
| D | 后悔厌恶 +20 |
| E | 冲动性 +20，策略稳定性 -15 |

### 13.9 动机追问题模板：单票重仓

```text
系统发现你在 {stock_name} 上曾经出现较高仓位。你当时为什么愿意集中持有这只股票？

A. 深入研究后认为确定性高
B. 它符合我的长期核心持仓计划
C. 亏损后不断补仓，仓位逐渐变大
D. 受他人推荐或市场热度影响后加大投入
E. 当时没有意识到仓位已经这么高
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 研究驱动 +15，集中容忍 +10 |
| B | 长期计划 +20 |
| C | 仓位失控 +20，回本心理 +10 |
| D | 从众 +15，风险意识 -10 |
| E | 风险意识 -20，仓位管理 -20 |

### 13.10 事后复盘题模板

```text
现在回看这段交易，你认为最大的问题是什么？

A. 买入理由不够清晰
B. 仓位控制不合理
C. 没有止损或退出规则
D. 信息来源不可靠
E. 我认为没有明显问题，亏损主要是市场原因
```

人格分影响：

| 选项 | 影响 |
|---|---|
| A | 自我反思 +15 |
| B | 风险意识 +15 |
| C | 规则意识 +15 |
| D | 信息质量意识 +15 |
| E | 外归因倾向 +20，自我修正 -15 |

---

## 14. 投资人格画像模型

### 14.1 画像维度

系统输出以下 10 个维度，每个维度 0-100 分。

| 维度 | 含义 |
|---|---|
| risk_capacity | 客观风险承受能力 |
| risk_preference | 主观风险偏好 |
| loss_aversion | 损失厌恶程度 |
| fomo_tendency | 踏空焦虑 / 追涨倾向 |
| overconfidence | 过度自信倾向 |
| trading_impulsiveness | 冲动交易倾向 |
| discipline | 交易纪律性 |
| holding_patience | 持有耐心 |
| concentration_tolerance | 集中持仓容忍度 |
| self_awareness | 自我认知一致性 |

### 14.2 评分来源权重

MVP 建议：

```text
最终人格分 =
交割单行为证据 × 70%
+ 用户回答 × 30%
```

原因：

- 交割单更接近真实行为。
- 回答用于解释行为动机。
- 如果行为和回答冲突，应以行为为主，并降低自我认知一致性。

### 14.3 行为证据到人格分映射

| 行为证据 | 影响维度 |
|---|---|
| 多次亏损补仓 | loss_aversion +, discipline -, overconfidence +/-, self_awareness 待回答 |
| 追涨买入 | fomo_tendency +, trading_impulsiveness + |
| 杀跌卖出 | loss_aversion +, holding_patience -, emotional_sensitivity + |
| 盈利早卖亏损久拿 | loss_aversion +, self_awareness -, discipline - |
| 卖出后追回 | fomo_tendency +, regret_aversion +, discipline - |
| 单票重仓 | concentration_tolerance +, overconfidence +, risk_capacity 需结合资金 |
| 高频交易 | trading_impulsiveness +, holding_patience -, discipline - |
| 热点切换 | fomo_tendency +, information_quality_risk + |

### 14.4 自我认知一致性

系统需要判断用户回答与交易行为是否一致。

示例：

用户回答：

> 我是长期价值投资者。

但行为显示：

```text
平均持仓周期 7 天
月换手率 300%
追涨买入比例高
卖出后追回频繁
```

系统结论：

```text
自我认知一致性：低
说明：用户自我描述偏长期，但实际交易行为更接近短线和趋势追逐。
```

### 14.5 自我认知一致性评分

```text
self_awareness_score =
100 - behavior_answer_conflict_score
```

冲突分示例：

| 冲突类型 | 加冲突分 |
|---|---:|
| 用户称有计划，但行为频繁无规则 | +20 |
| 用户称能承受亏损，但多次小亏快速卖出 | +20 |
| 用户称长期投资，但平均持仓 < 10 天 | +25 |
| 用户称分散投资，但单票仓位 > 35% | +20 |
| 用户否认系统观察，但交易证据强 | +15 |

### 14.6 投资人格类型

根据维度组合输出一个主类型和最多两个辅助标签。

| 人格类型 | 判定规则 | 说明 |
|---|---|---|
| 稳健防守型 | loss_aversion 高，risk_preference 低，holding_patience 中高 | 重视本金安全，适合低波动组合 |
| 情绪交易型 | loss_aversion 高，discipline 低，impulsiveness 高 | 容易因涨跌做临时决策 |
| 机会追逐型 | fomo 高，热点切换高，追涨多 | 容易受市场热度影响 |
| 回本补仓型 | 亏损补仓多，loss_aversion 高，discipline 低 | 容易越跌越买，仓位失控 |
| 研究驱动型 | 回答显示研究依据，交易周期稳定，纪律高 | 交易更依赖逻辑和计划 |
| 短线策略型 | 换手高，但规则性强，复盘能力强 | 可接受高频交易，但需纪律支持 |
| 集中进攻型 | concentration_tolerance 高，risk_preference 高 | 能承受集中波动，但需风险边界 |
| 长期复利型 | holding_patience 高，交易频率低，纪律高 | 更适合长期组合与再平衡 |

### 14.7 人格输出示例

```json
{
  "primary_persona": "回本补仓型",
  "secondary_tags": ["损失厌恶较高", "仓位管理偏弱"],
  "scores": {
    "risk_capacity": 55,
    "risk_preference": 68,
    "loss_aversion": 82,
    "fomo_tendency": 61,
    "overconfidence": 58,
    "trading_impulsiveness": 66,
    "discipline": 42,
    "holding_patience": 48,
    "concentration_tolerance": 72,
    "self_awareness": 53
  },
  "summary": "用户在亏损状态下持续加仓的行为较明显，且仓位上升较快。结合回答，用户存在一定回本心理和仓位管理风险。"
}
```

---

## 15. 当前持仓适配分析

### 15.1 目标

判断当前持仓是否与用户人格、风险承受能力和历史交易行为匹配。

核心问题：

```text
不是这只股票好不好，而是这套持仓是否适合这个用户。
```

### 15.2 输入

```json
{
  "persona_scores": {},
  "current_holdings": [],
  "portfolio_metrics": {},
  "selected_behavior_segments": [],
  "user_answers": []
}
```

### 15.3 当前持仓风险指标

| 指标 | 说明 |
|---|---|
| stock_count | 持仓股票数量 |
| max_single_position_weight | 最大单票仓位 |
| top3_position_weight | 前三大持仓占比 |
| sector_concentration | 最大行业占比 |
| portfolio_volatility_60d | 组合 60 日波动率 |
| portfolio_max_drawdown_60d | 组合 60 日最大回撤 |
| portfolio_beta | 相对大盘 beta |
| high_volatility_weight | 高波动资产占比 |
| loss_position_weight | 当前亏损持仓占比 |
| illiquid_position_weight | 流动性较差资产占比 |
| current_unrealized_pnl_pct | 当前浮盈浮亏 |
| overlap_with_past_behavior | 当前持仓是否延续历史问题行为 |

### 15.4 适配分析维度

输出 5 个适配分，每个 0-100。

| 分数 | 含义 |
|---|---|
| overall_suitability_score | 总体适配度 |
| risk_match_score | 风险承受匹配度 |
| behavior_match_score | 行为习惯匹配度 |
| concentration_match_score | 集中度匹配度 |
| holding_sustainability_score | 持有可持续性 |

### 15.5 总体适配度公式

```text
overall_suitability_score =
risk_match_score * 0.30
+ behavior_match_score * 0.25
+ concentration_match_score * 0.20
+ holding_sustainability_score * 0.15
+ self_awareness_adjustment * 0.10
```

其中：

```text
self_awareness_adjustment = self_awareness_score
```

### 15.6 风险承受匹配度

```text
risk_mismatch =
portfolio_max_drawdown_60d_abs - user_estimated_drawdown_tolerance
```

如果没有用户明确最大可承受回撤，则估算：

```text
estimated_drawdown_tolerance =
100 - loss_aversion * 0.4
+ risk_capacity * 0.3
+ risk_preference * 0.3
```

再映射为百分比：

| 估算分 | 最大可承受回撤估计 |
|---|---:|
| 0-30 | 5%-8% |
| 31-50 | 8%-12% |
| 51-70 | 12%-20% |
| 71-85 | 20%-30% |
| 86-100 | 30%+ |

风险匹配分：

```text
if portfolio_max_drawdown <= tolerance:
    risk_match_score = 85 + buffer_bonus
else:
    risk_match_score = max(0, 85 - (portfolio_max_drawdown - tolerance) * 300)
```

### 15.7 行为习惯匹配度

识别当前持仓是否会放大用户历史行为偏差。

| 人格/行为 | 不匹配持仓特征 |
|---|---|
| 损失厌恶高 | 高波动、高回撤、亏损持仓占比高 |
| FOMO 高 | 热门题材、短期涨幅大股票占比高 |
| 回本补仓型 | 当前亏损股票仓位高，且仍在加仓 |
| 冲动交易高 | 高波动小盘股、消息驱动股票 |
| 纪律性低 | 单票重仓、无明确退出规则 |
| 持有耐心低 | 长期逻辑但短期波动大的股票 |
| 过度自信高 | 高集中度组合、杠杆、单行业重仓 |

行为匹配分示例：

```text
behavior_risk_penalty = 0

if loss_aversion > 75 and high_volatility_weight > 0.5:
    behavior_risk_penalty += 20

if fomo_tendency > 70 and hot_sector_weight > 0.4:
    behavior_risk_penalty += 15

if discipline < 50 and max_single_position_weight > 0.3:
    behavior_risk_penalty += 20

if avg_down_behavior_score > 70 and loss_position_weight > 0.4:
    behavior_risk_penalty += 15

behavior_match_score = max(0, 100 - behavior_risk_penalty)
```

### 15.8 集中度匹配度

```text
concentration_penalty = 0

if max_single_position_weight > 0.2:
    concentration_penalty += 10

if max_single_position_weight > 0.35:
    concentration_penalty += 25

if top3_position_weight > 0.6:
    concentration_penalty += 15

if sector_concentration > 0.5:
    concentration_penalty += 15

if discipline < 50 and max_single_position_weight > 0.25:
    concentration_penalty += 10

concentration_match_score = max(0, 100 - concentration_penalty)
```

### 15.9 持有可持续性

判断用户是否可能坚持当前组合。

```text
holding_sustainability_score =
100
- volatility_pressure_penalty
- unrealized_loss_pressure_penalty
- behavior_conflict_penalty
- liquidity_need_penalty
```

示例规则：

| 条件 | 扣分 |
|---|---:|
| 高损失厌恶 + 当前浮亏 > 10% | -20 |
| 历史多次杀跌 + 当前高波动 | -15 |
| 历史频繁交易 + 当前长期组合 | -10 |
| 当前亏损持仓占比 > 50% | -15 |
| 当前最大单票亏损 > 20% | -10 |

---

## 16. 报告输出

### 16.1 报告结构

```text
1. 报告摘要
2. 投资人格画像
3. 代表性行为片段
4. 针对性问题与回答解读
5. 当前持仓适配度
6. 主要风险冲突
7. 行为偏差提醒
8. 持仓管理建议方向
9. 免责声明
```

### 16.2 报告摘要示例

```text
你的投资人格更接近“回本补仓型 + 机会追逐型”。

系统从你的交割单中识别出 4 个代表性行为片段：
1. 下跌后连续补仓
2. 短期上涨后追入
3. 盈利较小时快速卖出
4. 单票仓位集中

当前持仓与该人格的总体适配度为 56/100，属于中等偏低。主要冲突在于：你历史上对亏损较敏感，但当前组合中高波动和亏损持仓占比较高，可能导致后续市场下跌时出现情绪性补仓或卖出。
```

### 16.3 风险冲突表达模板

```text
系统观察到：
你的历史交易中存在 {behavior_type} 行为，而当前持仓中 {current_holding_feature}。

这可能带来的风险是：
当市场出现 {market_scenario} 时，你可能更容易出现 {behavior_risk}。

建议你重点关注：
{risk_management_direction}
```

示例：

```text
系统观察到：
你的历史交易中存在亏损后连续补仓行为，而当前持仓中已有 42% 处于浮亏状态。

这可能带来的风险是：
如果市场继续下跌，你可能为了降低成本而继续加仓，导致单票或单行业仓位进一步集中。

建议你重点关注：
提前设定单票仓位上限、补仓条件和退出规则，避免在情绪压力下临时决策。
```

### 16.4 适配度等级

| 分数 | 等级 | 解释 |
|---:|---|---|
| 80-100 | 高适配 | 当前持仓与人格、风险承受和行为模式较匹配 |
| 65-79 | 较适配 | 基本匹配，但存在局部风险 |
| 50-64 | 中等偏低 | 存在明显冲突，需要重点关注 |
| 35-49 | 低适配 | 当前持仓可能放大用户行为弱点 |
| 0-34 | 高风险不匹配 | 当前持仓与用户行为/风险承受严重冲突 |

---

## 17. 页面设计

### 17.1 页面一：上传交割单

核心元素：

- 上传按钮
- 支持格式说明
- 示例模板下载
- 隐私说明
- 风险与免责声明确认

用户操作：

1. 上传 CSV/Excel。
2. 勾选同意数据用于分析。
3. 点击“开始解析”。

验收标准：

- 支持 10MB 以内 CSV/Excel。
- 上传失败给出明确原因。
- 上传成功生成 `source_file_id`。

### 17.2 页面二：字段映射与解析确认

核心元素：

- 原始字段
- 系统识别字段
- 用户可手动修改映射
- 解析预览表
- 异常记录提示

验收标准：

- 必填字段识别率 >= 90%。
- 用户可手动指定字段。
- 无法识别买卖方向时必须阻断。
- 可展示前 20 条解析记录。

### 17.3 页面三：交易行为分析中

展示内容：

```text
正在识别你的持仓周期
正在分析交易行为模式
正在选择代表性行为片段
正在生成针对性问题
```

注意：

- 不承诺过短时间。
- 若分析失败，展示失败原因。

### 17.4 页面四：行为片段确认与问题回答

每个片段展示：

```text
行为观察：
你在 {stock_name} 上出现了 {summary}

关键证据：
- 补仓次数：3 次
- 最大仓位：31%
- 最大浮亏：22%
- 当前状态：仍持有

问题 1：
这个描述是否符合你当时情况？

问题 2：
当时你这么做的主要原因是什么？

问题 3：
现在回看，你认为最大问题是什么？
```

用户操作：

- 单选回答。
- 可选择“我不记得”。
- 可补充文字说明。
- 可跳过单个问题，但会降低报告置信度。

验收标准：

- 默认生成 3-5 个片段。
- 每个片段 2-3 个问题。
- 总题数不超过 15。
- 用户完成率目标 >= 70%。

### 17.5 页面五：当前持仓确认

核心元素：

- 当前持仓上传
- 或从交割单估算当前持仓
- 用户确认仓位和市值
- 手动修改成本和当前价格

验收标准：

- 若无当前持仓，系统可只生成历史行为报告。
- 若有当前持仓，生成持仓适配分析。
- 当前持仓字段缺失时提示置信度降低。

### 17.6 页面六：分析报告

核心模块：

1. 总体适配度
2. 投资人格
3. 关键行为证据
4. 当前持仓冲突
5. 风险提醒
6. 行为改进建议
7. 报告可信度
8. 免责声明

---

## 18. API 设计

### 18.1 上传文件

```http
POST /api/v1/uploads/trade-statement
```

请求：

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "file_name": "statement.xlsx",
  "file_type": "xlsx"
}
```

响应：

```json
{
  "source_file_id": "FILE_001",
  "upload_status": "SUCCESS"
}
```

### 18.2 解析交割单

```http
POST /api/v1/trades/parse
```

请求：

```json
{
  "source_file_id": "FILE_001",
  "field_mapping": {
    "成交日期": "trade_date",
    "证券代码": "symbol",
    "买卖方向": "side",
    "成交数量": "quantity",
    "成交价格": "price",
    "成交金额": "gross_amount"
  }
}
```

响应：

```json
{
  "parse_job_id": "JOB_001",
  "status": "PROCESSING"
}
```

### 18.3 获取解析结果

```http
GET /api/v1/trades/parse-result/{parse_job_id}
```

响应：

```json
{
  "status": "SUCCESS",
  "total_rows": 1200,
  "valid_rows": 1185,
  "invalid_rows": 15,
  "warnings": [
    "15 条记录缺少手续费，已按 0 处理"
  ]
}
```

### 18.4 生成持仓周期

```http
POST /api/v1/position-cycles/build
```

请求：

```json
{
  "user_id": "U001",
  "account_id": "A001"
}
```

响应：

```json
{
  "cycle_job_id": "CYCLE_JOB_001",
  "status": "SUCCESS",
  "cycle_count": 42
}
```

### 18.5 识别行为片段

```http
POST /api/v1/behavior-segments/detect
```

请求：

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "detect_types": [
    "LOSS_AVERAGING_DOWN",
    "CHASING_UP",
    "PANIC_SELL",
    "DISPOSITION_EFFECT",
    "REBUY_AFTER_SELL",
    "CONCENTRATION"
  ]
}
```

响应：

```json
{
  "candidate_count": 18,
  "selected_count": 5,
  "selected_segments": []
}
```

### 18.6 生成问题

```http
POST /api/v1/questions/generate
```

请求：

```json
{
  "user_id": "U001",
  "selected_segment_ids": [
    "SEG_001",
    "SEG_002"
  ]
}
```

响应：

```json
{
  "questionnaire_id": "Q_001",
  "questions": []
}
```

### 18.7 提交回答

```http
POST /api/v1/questions/submit
```

请求：

```json
{
  "questionnaire_id": "Q_001",
  "answers": [
    {
      "question_id": "Q1",
      "selected_option": "C",
      "free_text": "当时想摊低成本"
    }
  ]
}
```

响应：

```json
{
  "status": "SUCCESS"
}
```

### 18.8 生成人格画像

```http
POST /api/v1/persona/generate
```

请求：

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "questionnaire_id": "Q_001"
}
```

响应：

```json
{
  "persona_id": "P_001",
  "primary_persona": "回本补仓型",
  "scores": {}
}
```

### 18.9 当前持仓适配分析

```http
POST /api/v1/portfolio/suitability
```

请求：

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "persona_id": "P_001",
  "holding_snapshot_id": "H_001"
}
```

响应：

```json
{
  "suitability_id": "S_001",
  "overall_suitability_score": 56,
  "risk_conflicts": []
}
```

### 18.10 生成报告

```http
POST /api/v1/reports/generate
```

请求：

```json
{
  "user_id": "U001",
  "account_id": "A001",
  "persona_id": "P_001",
  "suitability_id": "S_001"
}
```

响应：

```json
{
  "report_id": "R_001",
  "status": "SUCCESS",
  "report_url": "/reports/R_001"
}
```

---

## 19. 数据库表设计

### 19.1 uploads

| 字段 | 类型 | 说明 |
|---|---|---|
| source_file_id | varchar | 文件 ID |
| user_id | varchar | 用户 ID |
| account_id | varchar | 账户 ID |
| file_name | varchar | 文件名 |
| file_type | varchar | 文件类型 |
| file_size | int | 文件大小 |
| upload_time | datetime | 上传时间 |
| status | varchar | 状态 |

### 19.2 normalized_trades

| 字段 | 类型 |
|---|---|
| trade_id | varchar |
| user_id | varchar |
| account_id | varchar |
| trade_date | datetime |
| symbol | varchar |
| stock_name | varchar |
| exchange | varchar |
| side | varchar |
| quantity | decimal |
| price | decimal |
| gross_amount | decimal |
| fee | decimal |
| tax | decimal |
| net_amount | decimal |
| currency | varchar |
| trade_type | varchar |
| active_trade | boolean |
| source_file_id | varchar |

### 19.3 position_cycles

| 字段 | 类型 |
|---|---|
| cycle_id | varchar |
| user_id | varchar |
| account_id | varchar |
| symbol | varchar |
| stock_name | varchar |
| start_date | date |
| end_date | date |
| status | varchar |
| trade_count | int |
| buy_count | int |
| sell_count | int |
| max_position_weight | decimal |
| max_drawdown_pct | decimal |
| realized_pnl_pct | decimal |
| unrealized_pnl_pct | decimal |
| hold_days | int |
| is_current_holding | boolean |

### 19.4 behavior_segments

| 字段 | 类型 |
|---|---|
| segment_id | varchar |
| user_id | varchar |
| account_id | varchar |
| cycle_id | varchar |
| behavior_type | varchar |
| symbol | varchar |
| stock_name | varchar |
| start_date | date |
| end_date | date |
| summary | text |
| evidence_json | json |
| scores_json | json |
| segment_score | decimal |
| confidence | varchar |
| selected | boolean |

### 19.5 questionnaires

| 字段 | 类型 |
|---|---|
| questionnaire_id | varchar |
| user_id | varchar |
| account_id | varchar |
| created_at | datetime |
| status | varchar |
| selected_segment_ids | json |

### 19.6 questions

| 字段 | 类型 |
|---|---|
| question_id | varchar |
| questionnaire_id | varchar |
| segment_id | varchar |
| question_type | varchar |
| question_text | text |
| options_json | json |
| scoring_json | json |
| display_order | int |

### 19.7 user_answers

| 字段 | 类型 |
|---|---|
| answer_id | varchar |
| question_id | varchar |
| user_id | varchar |
| selected_option | varchar |
| free_text | text |
| submitted_at | datetime |

### 19.8 persona_scores

| 字段 | 类型 |
|---|---|
| persona_id | varchar |
| user_id | varchar |
| account_id | varchar |
| primary_persona | varchar |
| secondary_tags | json |
| scores_json | json |
| summary | text |
| confidence | varchar |
| created_at | datetime |

### 19.9 holding_snapshots

| 字段 | 类型 |
|---|---|
| holding_snapshot_id | varchar |
| user_id | varchar |
| account_id | varchar |
| snapshot_date | date |
| holdings_json | json |
| total_market_value | decimal |
| cash_balance | decimal |
| confidence | varchar |

### 19.10 suitability_reports

| 字段 | 类型 |
|---|---|
| suitability_id | varchar |
| user_id | varchar |
| account_id | varchar |
| persona_id | varchar |
| holding_snapshot_id | varchar |
| scores_json | json |
| risk_conflicts_json | json |
| recommendations_json | json |
| created_at | datetime |

---

## 20. 核心算法伪代码

### 20.1 主流程

```python
def run_analysis(user_id, account_id, source_file_id, holding_snapshot=None):
    raw_file = load_file(source_file_id)

    normalized_trades = parse_and_normalize(raw_file)

    validate_trades(normalized_trades)

    position_cycles = build_position_cycles(normalized_trades)

    market_data = load_market_data(position_cycles)

    candidate_segments = detect_behavior_segments(
        position_cycles=position_cycles,
        trades=normalized_trades,
        market_data=market_data,
        holding_snapshot=holding_snapshot
    )

    scored_segments = score_segments(candidate_segments)

    selected_segments = select_representative_segments(scored_segments)

    questionnaire = generate_questions(selected_segments)

    return {
        "position_cycles": position_cycles,
        "selected_segments": selected_segments,
        "questionnaire": questionnaire
    }
```

### 20.2 候选片段识别

```python
def detect_behavior_segments(position_cycles, trades, market_data, holding_snapshot):
    candidates = []

    for cycle in position_cycles:
        candidates.extend(detect_loss_averaging_down(cycle, market_data))
        candidates.extend(detect_chasing_up(cycle, market_data))
        candidates.extend(detect_panic_sell(cycle, market_data))
        candidates.extend(detect_rebuy_after_sell(cycle, market_data))
        candidates.extend(detect_concentration(cycle, holding_snapshot))

    candidates.extend(detect_disposition_effect(position_cycles))
    candidates.extend(detect_frequent_trading(trades, position_cycles))
    candidates.extend(detect_hot_sector_switching(trades, market_data))

    return candidates
```

### 20.3 片段评分

```python
def calculate_segment_score(segment):
    score = (
        segment.behavior_intensity_score * 0.30
        + segment.capital_impact_score * 0.25
        + segment.emotion_signal_score * 0.20
        + segment.recency_score * 0.10
        + segment.current_position_score * 0.10
        + segment.explainability_score * 0.05
        - segment.noise_penalty
    )

    return max(0, min(100, score))
```

### 20.4 人格画像生成

```python
def generate_persona(selected_segments, user_answers):
    behavior_scores = infer_scores_from_segments(selected_segments)
    answer_scores = infer_scores_from_answers(user_answers)

    final_scores = {}

    for dimension in PERSONA_DIMENSIONS:
        final_scores[dimension] = (
            behavior_scores[dimension] * 0.70
            + answer_scores[dimension] * 0.30
        )

    self_awareness = calculate_self_awareness(
        selected_segments,
        user_answers
    )

    final_scores["self_awareness"] = self_awareness

    primary_persona = classify_persona(final_scores)

    return {
        "primary_persona": primary_persona,
        "scores": final_scores
    }
```

### 20.5 持仓适配分析

```python
def analyze_portfolio_suitability(persona, holding_snapshot, market_data):
    portfolio_metrics = calculate_portfolio_metrics(
        holding_snapshot,
        market_data
    )

    risk_match_score = calculate_risk_match_score(
        persona,
        portfolio_metrics
    )

    behavior_match_score = calculate_behavior_match_score(
        persona,
        portfolio_metrics
    )

    concentration_match_score = calculate_concentration_match_score(
        persona,
        portfolio_metrics
    )

    holding_sustainability_score = calculate_holding_sustainability(
        persona,
        portfolio_metrics
    )

    overall_score = (
        risk_match_score * 0.30
        + behavior_match_score * 0.25
        + concentration_match_score * 0.20
        + holding_sustainability_score * 0.15
        + persona["scores"]["self_awareness"] * 0.10
    )

    conflicts = generate_risk_conflicts(
        persona,
        portfolio_metrics
    )

    return {
        "overall_suitability_score": overall_score,
        "risk_match_score": risk_match_score,
        "behavior_match_score": behavior_match_score,
        "concentration_match_score": concentration_match_score,
        "holding_sustainability_score": holding_sustainability_score,
        "risk_conflicts": conflicts
    }
```

---

## 21. 异常与边界场景

### 21.1 交易样本不足

条件：

```text
主动交易笔数 < 10
或持仓周期 < 3
```

处理：

- 继续生成报告。
- 报告标记“样本不足，结论仅供参考”。
- 问题更多依赖有限片段。
- 不输出强结论。

### 21.2 没有当前持仓

处理：

- 生成历史行为画像。
- 不生成当前持仓适配度。
- 提示用户上传当前持仓可获得完整分析。

### 21.3 缺少行情数据

处理：

- 无法判断追涨、卖出后反弹等行情依赖行为。
- 仍可判断补仓、频繁交易、集中度。
- 降低报告置信度。

### 21.4 用户否认系统观察

处理：

- 记录为 `observation_disputed = true`。
- 不强制采用该片段结论。
- 降低该片段权重。
- 如果多个强证据被否认，则降低自我认知一致性。

### 21.5 多账户问题

MVP：

- 单次只分析一个账户。
- 若用户上传多个账户，要求选择一个账户。
- 后续版本支持合并分析。

### 21.6 融资融券

MVP：

- 如果交割单中识别到融资、融券、杠杆字段，则标记风险。
- 不做完整保证金计算。
- 在报告中提示“杠杆数据未完整纳入，风险可能被低估”。

---

## 22. 安全、隐私与合规

### 22.1 隐私要求

- 用户上传交割单前必须展示隐私说明。
- 交割单属于敏感金融数据，需要加密存储。
- 不得将用户原始交易数据用于公开模型训练，除非用户明确同意。
- 报告中展示股票代码和名称时，允许用户选择脱敏。
- 支持用户删除上传文件和分析结果。

### 22.2 数据脱敏

报告分享模式：

```text
股票名称：可隐藏
股票代码：可隐藏中间位
金额：可转换为比例
账户资产：默认不展示绝对金额
```

示例：

```text
某股票 A：最大仓位 31%，最大浮亏 22%
```

而不是：

```text
600000 浦发银行：投入 310,000 元
```

### 22.3 合规免责声明

每份报告必须包含：

```text
本报告基于用户提供的交易记录、持仓数据及系统规则生成，仅用于投资行为复盘、风险识别和投资者教育，不构成任何证券、基金、期货或其他金融产品的投资建议。报告中的风险提示不代表对任何证券价格、收益或未来表现的预测。用户应结合自身情况独立判断，必要时咨询具备资质的专业投资顾问。
```

### 22.4 禁止输出

系统不得输出：

- 明确买入某只股票
- 明确卖出某只股票
- 推荐替代股票
- 保证收益
- 预测涨跌
- 根据人格标签做绝对判断
- 使用侮辱性人格描述

---

## 23. 指标体系

### 23.1 产品指标

| 指标 | 定义 | MVP 目标 |
|---|---|---:|
| 上传成功率 | 成功上传文件 / 尝试上传文件 | >= 90% |
| 解析成功率 | 成功解析文件 / 上传文件 | >= 80% |
| 字段自动识别率 | 自动识别字段 / 必填字段 | >= 90% |
| 问卷完成率 | 完成回答用户 / 进入问卷用户 | >= 70% |
| 报告生成成功率 | 成功生成报告 / 提交分析用户 | >= 90% |
| 报告查看完成率 | 查看报告超过 60 秒用户比例 | >= 60% |

### 23.2 分析质量指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| 片段认可率 | 用户选择“完全符合/基本符合”的片段比例 | >= 70% |
| 片段争议率 | 用户选择“不太符合”的片段比例 | <= 20% |
| 问题相关度 | 用户评分认为问题相关 | >= 4/5 |
| 报告有用度 | 用户评分认为报告有用 | >= 4/5 |
| 重复片段率 | 同类同股重复片段比例 | <= 10% |

### 23.3 技术指标

| 指标 | 目标 |
|---|---:|
| 1000 条交易解析时间 | < 10 秒 |
| 1000 条交易行为识别时间 | < 15 秒 |
| 报告生成时间 | < 30 秒 |
| API P95 响应时间 | < 2 秒，异步任务除外 |
| 文件解析失败可解释率 | >= 95% |

---

## 24. 验收标准

### 24.1 文件解析验收

给定 5 种不同券商 CSV/Excel 样例：

- 系统能识别必填字段。
- 系统能正确标准化买卖方向。
- 系统能过滤非主动交易。
- 系统能输出错误行原因。
- 解析结果可供用户确认。

### 24.2 持仓周期验收

给定一组交易：

```text
3/1 买入 A 1000 股
3/8 买入 A 1000 股
3/15 卖出 A 500 股
4/1 卖出 A 1500 股
5/1 买入 A 1000 股
```

系统应生成两个持仓周期：

```text
周期 1：3/1 - 4/1
周期 2：5/1 - 当前或清仓日
```

### 24.3 亏损补仓识别验收

给定：

```text
首次买入后下跌 8%
随后补仓 2 次
最大仓位 25%
最大浮亏 18%
```

系统应识别：

```text
behavior_type = LOSS_AVERAGING_DOWN
segment_score >= 70
question_theme 包含 补仓动机、仓位管理
```

### 24.4 追涨识别验收

给定：

```text
买入前 10 日涨幅 22%
买入后 10 日亏损 7%
```

系统应识别：

```text
behavior_type = CHASING_UP
心理假设包含 FOMO / 趋势确认
```

### 24.5 多样性选择验收

给定候选片段：

```text
5 个亏损补仓
2 个追涨
1 个单票重仓
1 个卖出后追回
```

系统不能选择 5 个亏损补仓。  
输出中同类行为最多 2 个，并至少覆盖 3 种行为类型。

### 24.6 问题生成验收

每个选中片段必须生成：

- 事实确认题
- 动机追问题
- 复盘或风险预问题

每个问题必须包含：

- 具体股票或片段描述
- 明确选项
- 对应评分映射

### 24.7 报告验收

报告必须包含：

- 投资人格主标签
- 10 个维度分
- 3-5 个代表性行为片段
- 当前持仓适配度
- 主要风险冲突
- 免责声明

报告不得包含：

- 个股买入建议
- 个股卖出建议
- 收益承诺
- 价格预测

---

## 25. MVP 研发里程碑

### 阶段一：数据接入与解析

目标：

- 支持 CSV/Excel 上传。
- 完成字段映射。
- 生成标准交易表。

交付物：

- 文件上传接口
- 字段映射页面
- `normalized_trades` 表
- 解析异常处理

### 阶段二：持仓周期与基础指标

目标：

- 按股票构建持仓周期。
- 计算成本、盈亏、持仓天数、最大仓位。

交付物：

- `position_cycles` 表
- 成本计算模块
- 仓位估算模块
- 周期可视化调试工具

### 阶段三：行为片段识别

目标：

- 支持 6 类核心行为检测。
- 生成候选片段和分数。

交付物：

- 行为检测器
- `behavior_segments` 表
- 片段评分模块
- 多样性选择器

### 阶段四：问题生成与回答

目标：

- 根据片段生成问题。
- 用户回答后影响人格评分。

交付物：

- 问题模板库
- 问卷页面
- `questions` / `user_answers` 表
- 回答评分模块

### 阶段五：人格画像与持仓适配

目标：

- 生成 10 维人格分。
- 分析当前持仓适配度。

交付物：

- 人格评分模块
- 当前持仓上传/确认页面
- 持仓适配评分模块
- 风险冲突生成器

### 阶段六：报告生成

目标：

- 输出完整分析报告。

交付物：

- 报告页面
- PDF/Markdown 导出，后续可选
- 免责声明
- 用户反馈入口

---

## 26. 后续版本规划

### V1.1

- 支持 PDF 交割单解析
- 支持 OCR 截图识别
- 支持更多券商模板
- 行为片段可视化时间线
- 用户手动标记交易原因

### V1.2

- 接入券商 API
- 支持自动同步交易
- 支持多账户合并
- 支持基金、ETF、可转债

### V1.3

- 加入市场环境识别
- 区分牛市、熊市、震荡市行为
- 加入同类用户行为对比
- 加入行为改善追踪

### V2.0

- 长期行为画像
- 定期持仓适配提醒
- 个性化投教课程
- 风险预警系统
- 投顾工作台

---

## 27. 关键风险与应对

### 27.1 用户误解为投资建议

风险：

- 用户可能认为报告是在建议买卖。

应对：

- 所有输出使用“风险提示”“适配分析”“建议关注”。
- 不输出具体买卖指令。
- 每页报告包含免责声明。
- 对高风险结论使用解释性语言。

### 27.2 交割单解析错误

风险：

- 字段映射错误导致行为误判。

应对：

- 解析后必须让用户确认。
- 高风险结论引用证据。
- 支持用户反馈“该观察不准确”。

### 27.3 行为误判

风险：

- 价值投资式补仓被误判为回本心理。

应对：

- 所有心理判断必须通过问题追问。
- 输出“可能反映”，不输出“必然说明”。
- 用户回答可修正模型判断。

### 27.4 数据不足

风险：

- 交易记录太少，结论不可靠。

应对：

- 输出置信度。
- 明确提示样本不足。
- 不生成强人格标签。

### 27.5 用户隐私担忧

风险：

- 用户不愿上传真实交割单。

应对：

- 支持脱敏上传。
- 支持本地解析方案，后续版本。
- 报告默认使用比例，不展示金额。
- 支持删除数据。

---

## 28. 示例：完整分析链路

### 28.1 输入交易

```text
2025-03-01 买入 A 股票，仓位 8%，价格 10.00
2025-03-08 买入 A 股票，仓位升至 16%，价格 9.20
2025-03-15 买入 A 股票，仓位升至 31%，价格 8.10
2025-04-01 A 股票价格 7.80，仍持有
```

### 28.2 系统识别

```json
{
  "behavior_type": "LOSS_AVERAGING_DOWN",
  "summary": "用户在 A 股票下跌过程中连续补仓 2 次，仓位从 8% 提升至 31%，最大浮亏约 22%。",
  "scores": {
    "behavior_intensity_score": 88,
    "capital_impact_score": 78,
    "emotion_signal_score": 85,
    "segment_score": 84
  }
}
```

### 28.3 系统生成问题

```text
系统观察到：
你在 A 股票下跌过程中连续补仓 2 次，仓位从 8% 提升至 31%，期间最大浮亏约 22%。

问题 1：
这个描述是否符合你当时的交易情况？
A. 完全符合
B. 基本符合
C. 不太符合
D. 不记得

问题 2：
当时你继续加仓的主要原因是什么？
A. 我重新评估后认为公司价值更有吸引力
B. 我原本就计划分批建仓，并有明确仓位上限
C. 我主要想降低持仓成本，等待反弹回本
D. 我不愿意承认前面买错了
E. 当时没有明确计划，只是觉得跌多了会涨

问题 3：
现在回看这段交易，你认为最大的问题是什么？
A. 买入理由不够清晰
B. 仓位控制不合理
C. 没有止损或退出规则
D. 信息来源不可靠
E. 我认为没有明显问题，亏损主要是市场原因
```

### 28.4 用户回答

```text
问题 1：A
问题 2：C
问题 3：B
```

### 28.5 系统画像

```text
投资人格：回本补仓型
损失厌恶：高
仓位管理：偏弱
自我反思能力：中等
交易纪律：偏低
```

### 28.6 当前持仓适配结论

```text
当前组合适配度：52/100，中等偏低。

主要冲突：
用户历史上存在亏损后连续补仓行为，当前持仓中仍有较高比例股票处于浮亏状态。如果市场继续下跌，用户可能继续补仓以降低成本，导致仓位进一步集中。

建议关注：
1. 为每只股票设定最大仓位上限。
2. 补仓前要求满足明确条件，而不是仅因下跌。
3. 提前设定退出规则。
4. 避免在亏损压力下临时扩大仓位。
```

---

## 29. 开发优先级

### P0

- CSV/Excel 上传
- 字段映射
- 交易标准化
- 持仓周期构建
- 亏损补仓识别
- 追涨识别
- 单票重仓识别
- 片段评分
- Top 3-5 选择
- 问题生成
- 基础人格画像
- 基础报告

### P1

- 杀跌卖出识别
- 盈利早卖 / 亏损久拿识别
- 卖出后追回识别
- 频繁交易识别
- 当前持仓适配度
- 报告置信度
- 用户反馈修正

### P2

- 热点切换识别
- 行业数据接入
- 板块热度计算
- PDF 解析
- 图表可视化
- 导出报告

---

## 30. 最小可上线版本定义

最小可上线版本必须满足：

1. 用户可上传 CSV/Excel 交割单。
2. 系统可成功解析主动买卖交易。
3. 系统可生成持仓周期。
4. 系统可识别至少 3 类行为：
   - 亏损补仓
   - 追涨买入
   - 单票重仓
5. 系统可选出 3 个代表性片段。
6. 系统可为每个片段生成 3 道问题。
7. 用户回答后可生成基础人格画像。
8. 用户上传当前持仓后可生成基础适配评分。
9. 报告不包含具体买卖建议。
10. 报告包含免责声明。

---

## 31. 待确认问题

1. 首期支持哪些市场？
   - A 股
   - 港股
   - 美股
   - 还是先支持单一市场？

2. 是否有稳定行情数据源？
   - 日线行情
   - 复权价格
   - 行业分类
   - 板块收益

3. 用户是否能提供账户总资产？
   - 如果不能，仓位只能估算。

4. 是否需要支持券商 PDF？
   - 如果首期支持，会显著增加解析复杂度。

5. 报告是否允许展示具体股票名称？
   - 默认展示，分享时脱敏。

6. 是否需要 B 端投顾工作台？
   - 如果需要，权限、客户管理和合规留痕要提前设计。

7. 是否需要保留用户原始文件？
   - 可设计为解析后删除原文件，仅保留结构化数据。

---

## 32. 附录：行为类型枚举

```json
{
  "LOSS_AVERAGING_DOWN": "亏损补仓",
  "CHASING_UP": "追涨买入",
  "PANIC_SELL": "杀跌卖出",
  "DISPOSITION_EFFECT": "盈利早卖/亏损久拿",
  "REBUY_AFTER_SELL": "卖出后追回",
  "CONCENTRATION": "单票重仓",
  "FREQUENT_TRADING": "频繁交易",
  "HOT_SECTOR_SWITCHING": "热点切换"
}
```

---

## 33. 附录：人格维度枚举

```json
{
  "risk_capacity": "客观风险承受能力",
  "risk_preference": "主观风险偏好",
  "loss_aversion": "损失厌恶程度",
  "fomo_tendency": "踏空焦虑/追涨倾向",
  "overconfidence": "过度自信倾向",
  "trading_impulsiveness": "冲动交易倾向",
  "discipline": "交易纪律性",
  "holding_patience": "持有耐心",
  "concentration_tolerance": "集中持仓容忍度",
  "self_awareness": "自我认知一致性"
}
```

---

## 34. 附录：报告免责声明

```text
本报告基于用户提供的交易记录、持仓数据及系统规则生成，仅用于投资行为复盘、风险识别和投资者教育，不构成任何证券、基金、期货或其他金融产品的投资建议。报告中的风险提示不代表对任何证券价格、收益或未来表现的预测。用户应结合自身情况独立判断，必要时咨询具备资质的专业投资顾问。市场有风险，投资需谨慎。
```

---

## 35. 一句话总结

本产品的核心不是判断“哪只股票好”，而是判断：

> 用户真实交易行为、投资人格和当前持仓风险之间是否匹配。

真正的产品壁垒在于：

1. 能从交割单中找到最能说明问题的行为片段。
2. 能基于真实行为提出用户难以回避的问题。
3. 能把行为证据、用户动机和当前持仓风险连接起来。
4. 能在不直接荐股的前提下提供有价值的风险适配分析。
