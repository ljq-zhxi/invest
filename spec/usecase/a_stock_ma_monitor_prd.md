# A股均线监控脚本 PRD

## 1. 背景

需要一个可重复运行的监控脚本，用于获取指定 A 股股票列表在最近一个交易日的收盘价，并计算其 5 日、10 日、20 日、30 日、60 日均线价格。脚本运行后生成一份 HTML 报告，清晰展示每只股票当前价格相对于各均线的位置，例如“站上 5 日线”“跌破 20 日线”等，方便快速判断股票短中期趋势状态。

数据源优先使用新浪财经，也可预留后续切换到其他行情源的能力。

---

## 2. 目标

脚本每次运行时完成以下任务：

1. 读取 A 股股票列表。
2. 获取每只股票最近至少 60 个交易日的历史收盘价。
3. 识别最近一个交易日。
4. 输出最近一个交易日的收盘价。
5. 计算 5 日、10 日、20 日、30 日、60 日均线价格。
6. 判断当前收盘价位于各均线的上方、下方或附近。
7. 生成 HTML 报告。
8. 支持异常股票、停牌、数据缺失等情况的提示。
9. 基于历史 K 线统计上升趋势回踩均线、走弱趋势跌破均线的次数，并输出趋势日志。
10. 基于当前价格计算相较最近一个极值高点的回撤幅度，并输出计算日志。

---

## 3. 使用场景

### 3.1 手动运行

用户在本地或服务器执行脚本：

```bash
python stock_ma_monitor.py
```

脚本生成：

```bash
output/a_stock_ma_report.html
```

用户打开 HTML 查看结果。

### 3.2 定时运行

可通过 crontab、Windows 任务计划程序、Airflow 或其他调度工具每日收盘后运行，例如：

```bash
30 16 * * 1-5 python /path/stock_ma_monitor.py
```

---

## 4. 输入

### 4.1 股票列表配置

支持通过配置文件维护股票列表。

文件名示例：

```bash
stocks.csv
```

字段设计：

| 字段 | 必填 | 说明 |
|---|---:|---|
| code | 是 | 股票代码，例如 600519、000001 |
| name | 否 | 股票名称，例如 贵州茅台、平安银行 |
| market | 否 | 市场，sh 或 sz；如为空则自动识别 |

示例：

```csv
code,name,market
600519,贵州茅台,sh
000001,平安银行,sz
300750,宁德时代,sz
```

### 4.2 配置文件

文件名示例：

```bash
config.yaml
```

示例：

```yaml
data_source: sina
ma_windows: [5, 10, 20, 30, 60]
near_threshold_pct: 0.3
output_path: output/a_stock_ma_report.html
request_timeout_seconds: 10
retry_times: 3
```

字段说明：

| 字段 | 默认值 | 说明 |
|---|---:|---|
| data_source | sina | 行情数据源 |
| ma_windows | [5,10,20,30,60] | 均线周期 |
| near_threshold_pct | 0.3 | 判断“接近均线”的百分比阈值 |
| output_path | output/a_stock_ma_report.html | HTML 输出路径 |
| request_timeout_seconds | 10 | 请求超时时间 |
| retry_times | 3 | 请求失败重试次数 |

---

## 5. 数据源要求

### 5.1 新浪财经数据源

优先支持新浪财经。

脚本需要支持以下能力：

1. 根据股票代码获取历史日 K 数据。
2. 至少返回最近 60 个有效交易日的收盘价。
3. 包含日期、开盘价、最高价、最低价、收盘价、成交量等字段。
4. 能够处理停牌、无数据、接口异常等情况。

### 5.2 数据源抽象

为了后续扩展，应设计统一的数据源接口。

```python
class StockDataSource:
    def get_daily_bars(self, code: str, market: str, limit: int = 80):
        pass
```

返回数据结构建议：

```python
[
    {
        "date": "2026-05-12",
        "open": 100.0,
        "high": 102.0,
        "low": 99.5,
        "close": 101.2,
        "volume": 12345678
    }
]
```

---

## 6. 核心计算逻辑

### 6.1 最近交易日收盘价

对于每只股票，按交易日期升序或降序排序，取最新一条有效 K 线数据的 `close` 作为当前价格。

```text
current_close = latest_daily_bar.close
```

### 6.2 均线计算

以最近 N 个交易日的收盘价计算简单移动平均线。

```text
MA_N = 最近 N 个交易日收盘价之和 / N
```

需要计算：

| 均线 | 周期 |
|---|---:|
| MA5 | 5 日 |
| MA10 | 10 日 |
| MA20 | 20 日 |
| MA30 | 30 日 |
| MA60 | 60 日 |

### 6.3 上线 / 下线判断

对于每条均线，比较当前收盘价和均线价格。

```text
diff_pct = (current_close - ma_price) / ma_price * 100
```

判断规则：

| 条件 | 状态 |
|---|---|
| diff_pct > near_threshold_pct | 线上 |
| diff_pct < -near_threshold_pct | 线下 |
| abs(diff_pct) <= near_threshold_pct | 贴近 |

默认 `near_threshold_pct = 0.3`。

示例：

| 当前价 | MA20 | 差异 | 状态 |
|---:|---:|---:|---|
| 101.00 | 100.00 | +1.00% | 20 日线上 |
| 99.50 | 100.00 | -0.50% | 20 日线下 |
| 100.20 | 100.00 | +0.20% | 贴近 20 日线 |

---

## 7. 输出 HTML 要求

### 7.1 文件输出

每次运行生成一个 HTML 文件：

```bash
output/a_stock_ma_report.html
```

可选支持按日期归档：

```bash
output/a_stock_ma_report_20260513.html
```

### 7.2 页面标题

```text
A股均线监控报告
```

### 7.3 页面头部信息

HTML 顶部展示：

| 字段 | 说明 |
|---|---|
| 报告生成时间 | 脚本运行时间 |
| 最近交易日 | 数据中识别出的最新交易日 |
| 股票数量 | 总股票数 |
| 成功数量 | 成功获取并计算数量 |
| 失败数量 | 数据缺失或接口异常数量 |
| 数据源 | 新浪财经 |

### 7.4 主表格字段

HTML 表格字段如下：

| 字段 | 说明 |
|---|---|
| 股票代码 | 例如 600519 |
| 股票名称 | 例如 贵州茅台 |
| 最近交易日 | 例如 2026-05-12 |
| 收盘价 | 最近交易日收盘价 |
| MA5 | 5 日均线 |
| MA5 状态 | 线上 / 线下 / 贴近 |
| MA10 | 10 日均线 |
| MA10 状态 | 线上 / 线下 / 贴近 |
| MA20 | 20 日均线 |
| MA20 状态 | 线上 / 线下 / 贴近 |
| MA30 | 30 日均线 |
| MA30 状态 | 线上 / 线下 / 贴近 |
| MA60 | 60 日均线 |
| MA60 状态 | 线上 / 线下 / 贴近 |
| 综合状态 | 多头 / 空头 / 震荡 / 数据不足 |
| 趋势分析 | 上升趋势回踩统计、走弱趋势跌破统计 |
| 极值回撤 | 当前价较最近极值高点下跌幅度 |
| 备注 | 停牌、缺失、异常说明 |

### 7.5 新增分析字段说明

1. 趋势分析（历史 K 线）

- 上升趋势：收盘价 > MA20 且 MA20 > MA60 的连续区间。
- 在上升趋势内，统计每日最低价回踩到各均线（MA5/10/20/30/60）的次数，并记录日志（日期、回踩到几日线）。
- 输出每段上升趋势“最多回踩到几日线”的结论。
- 走弱趋势：收盘价 < MA20 且 MA20 < MA60 的连续区间。
- 在走弱趋势内，统计每日收盘价跌破各均线（MA5/10/20/30/60）的次数，并记录日志（日期、跌破几日线）。
- 输出每段走弱趋势“一般跌破几日线”的结论。

2. 极值回撤（当前价格）

- 识别最近一个极值高点（默认使用最近局部高点）。
- 计算：

```text
drawdown_pct = (current_close - recent_peak_close) / recent_peak_close * 100
```

- 当 `drawdown_pct < 0` 时，按“下跌 X%”展示。
- 输出日志：相较于哪一天高点、该高点价格、当前价格、变化百分比。

---

## 8. 综合状态判断

### 8.1 多头排列

如果满足：

```text
收盘价 > MA5 > MA10 > MA20 > MA30 > MA60
```

则标记为：

```text
强多头
```

### 8.2 偏多

如果当前价格位于 MA20 和 MA60 之上，但均线未完全多头排列：

```text
收盘价 > MA20 且 收盘价 > MA60
```

则标记为：

```text
偏多
```

### 8.3 空头排列

如果满足：

```text
收盘价 < MA5 < MA10 < MA20 < MA30 < MA60
```

则标记为：

```text
强空头
```

### 8.4 偏空

如果当前价格低于 MA20 和 MA60，但均线未完全空头排列：

```text
收盘价 < MA20 且 收盘价 < MA60
```

则标记为：

```text
偏空
```

### 8.5 震荡

其他情况标记为：

```text
震荡
```

---

## 9. HTML 样式要求

### 9.1 状态颜色

| 状态 | 建议颜色 |
|---|---|
| 线上 | 红色 |
| 线下 | 绿色 |
| 贴近 | 橙色 |
| 强多头 | 深红色 |
| 偏多 | 红色 |
| 强空头 | 深绿色 |
| 偏空 | 绿色 |
| 震荡 | 灰色 |
| 数据不足 | 深灰色 |

说明：A 股常用红涨绿跌，因此“线上 / 偏多”使用红色，“线下 / 偏空”使用绿色。

### 9.2 表格功能

HTML 页面建议支持：

1. 按股票代码搜索。
2. 按综合状态筛选。
3. 点击表头排序。
4. 异常股票单独高亮。
5. 移动端可横向滚动。

---

## 10. 异常处理

### 10.1 数据不足

如果某股票有效交易日少于 60 日：

1. 能计算的均线正常输出。
2. 不能计算的均线显示 `N/A`。
3. 综合状态显示 `数据不足`。

### 10.2 停牌

如果最新交易日早于全市场最近交易日，标记：

```text
疑似停牌或未更新
```

### 10.3 接口失败

接口失败时：

1. 重试指定次数。
2. 仍失败则记录错误。
3. HTML 中该股票显示为异常。
4. 不影响其他股票计算。

### 10.4 股票代码无效

显示：

```text
股票代码无效或无行情数据
```

---

## 11. 脚本模块设计

建议目录结构：

```text
stock_ma_monitor/
├── stock_ma_monitor.py
├── config.yaml
├── stocks.csv
├── output/
│   └── a_stock_ma_report.html
├── data_sources/
│   ├── __init__.py
│   └── sina.py
├── services/
│   ├── calculator.py
│   ├── analyzer.py
│   └── html_renderer.py
└── logs/
    └── monitor.log
```

### 11.1 stock_ma_monitor.py

主入口，负责：

1. 读取配置。
2. 读取股票列表。
3. 调用数据源。
4. 调用均线计算。
5. 调用状态判断。
6. 生成 HTML。
7. 输出日志。

### 11.2 sina.py

负责新浪财经数据获取。

### 11.3 calculator.py

负责均线计算。

### 11.4 analyzer.py

负责线上 / 线下判断和综合状态判断。

### 11.5 html_renderer.py

负责生成 HTML 页面。

---

## 12. 输出数据结构

每只股票计算后形成如下结构：

```json
{
  "code": "600519",
  "name": "贵州茅台",
  "market": "sh",
  "latest_trade_date": "2026-05-12",
  "close": 1688.50,
  "ma": {
    "5": 1675.20,
    "10": 1662.30,
    "20": 1650.80,
    "30": 1642.10,
    "60": 1608.90
  },
  "ma_status": {
    "5": "线上",
    "10": "线上",
    "20": "线上",
    "30": "线上",
    "60": "线上"
  },
  "diff_pct": {
    "5": 0.79,
    "10": 1.58,
    "20": 2.28,
    "30": 2.82,
    "60": 4.95
  },
  "overall_status": "偏多",
  "remark": ""
}
```

---

## 13. 验收标准

### 13.1 功能验收

脚本运行后必须满足：

1. 能成功读取股票列表。
2. 能获取每只股票的历史日线数据。
3. 能正确识别最近一个交易日。
4. 能输出最近交易日收盘价。
5. 能计算 5、10、20、30、60 日均线。
6. 能判断当前价格处于各均线上方、下方或贴近。
7. 能生成可直接打开的 HTML 文件。
8. 单只股票失败不影响整体运行。

### 13.2 计算验收

对于任意股票，人工抽查：

```text
MA5 = 最近 5 个交易日收盘价平均值
MA10 = 最近 10 个交易日收盘价平均值
MA20 = 最近 20 个交易日收盘价平均值
MA30 = 最近 30 个交易日收盘价平均值
MA60 = 最近 60 个交易日收盘价平均值
```

脚本计算结果与人工计算结果误差不超过：

```text
0.01
```

### 13.3 HTML 验收

HTML 页面需要满足：

1. 表格字段完整。
2. 状态颜色清晰。
3. 支持搜索、筛选或排序中的至少一种。
4. 异常数据有明确提示。
5. 页面中展示报告生成时间和数据源。

---

## 14. 非功能要求

### 14.1 性能

在 500 只股票以内，脚本应在合理时间内完成。

建议目标：

```text
500 只股票 <= 5 分钟
```

### 14.2 稳定性

1. 网络请求需要设置超时。
2. 接口失败需要重试。
3. 接口返回异常格式时不能导致整个脚本崩溃。
4. 所有错误写入日志。

### 14.3 可维护性

1. 数据源模块和计算模块解耦。
2. 均线周期可配置。
3. HTML 模板和业务逻辑分离。
4. 后续可扩展邮件、企业微信、飞书通知。

---

## 15. 可选增强功能

后续版本可增加：

1. 发送邮件报告。
2. 企业微信 / 飞书机器人推送。
3. 输出 Excel。
4. 增加成交量均线。
5. 增加 MACD、KDJ、RSI 等指标。
6. 增加突破提醒，例如“首次站上 60 日线”。
7. 增加连续 N 日在线上 / 线下统计。
8. 增加行业、概念板块维度汇总。
9. 增加历史报告归档。
10. 增加本地缓存，减少重复请求。

---

## 16. 示例 HTML 展示

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>A股均线监控报告</title>
  <style>
    body {
      font-family: Arial, "Microsoft YaHei", sans-serif;
      margin: 24px;
      background: #f7f7f7;
      color: #222;
    }

    h1 {
      margin-bottom: 8px;
    }

    .summary {
      margin-bottom: 20px;
      padding: 12px 16px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      background: #fff;
      font-size: 14px;
    }

    th, td {
      border: 1px solid #ddd;
      padding: 8px 10px;
      text-align: right;
      white-space: nowrap;
    }

    th {
      background: #f0f0f0;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    td:first-child,
    td:nth-child(2),
    th:first-child,
    th:nth-child(2) {
      text-align: left;
    }

    .above {
      color: #c00000;
      font-weight: bold;
    }

    .below {
      color: #008000;
      font-weight: bold;
    }

    .near {
      color: #e69100;
      font-weight: bold;
    }

    .bull-strong {
      color: #990000;
      font-weight: bold;
    }

    .bull {
      color: #c00000;
      font-weight: bold;
    }

    .bear-strong {
      color: #006100;
      font-weight: bold;
    }

    .bear {
      color: #008000;
      font-weight: bold;
    }

    .neutral {
      color: #666;
      font-weight: bold;
    }

    .error {
      background: #fff2cc;
      color: #7f6000;
    }

    .table-wrapper {
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <h1>A股均线监控报告</h1>

  <div class="summary">
    <div>报告生成时间：2026-05-13 16:30:00</div>
    <div>最近交易日：2026-05-12</div>
    <div>数据源：新浪财经</div>
    <div>股票数量：3，成功：3，失败：0</div>
  </div>

  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>代码</th>
          <th>名称</th>
          <th>交易日</th>
          <th>收盘价</th>
          <th>MA5</th>
          <th>MA5状态</th>
          <th>MA10</th>
          <th>MA10状态</th>
          <th>MA20</th>
          <th>MA20状态</th>
          <th>MA30</th>
          <th>MA30状态</th>
          <th>MA60</th>
          <th>MA60状态</th>
          <th>综合状态</th>
          <th>备注</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>600519</td>
          <td>贵州茅台</td>
          <td>2026-05-12</td>
          <td>1688.50</td>
          <td>1675.20</td>
          <td class="above">线上</td>
          <td>1662.30</td>
          <td class="above">线上</td>
          <td>1650.80</td>
          <td class="above">线上</td>
          <td>1642.10</td>
          <td class="above">线上</td>
          <td>1608.90</td>
          <td class="above">线上</td>
          <td class="bull">偏多</td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>
</body>
</html>
```

---

## 17. 推荐实现优先级

### V1 必须实现

1. 读取股票列表。
2. 获取历史收盘价。
3. 计算 5、10、20、30、60 日均线。
4. 判断线上 / 线下 / 贴近。
5. 生成 HTML 报告。
6. 基础异常处理。

### V2 增强

1. 排序、搜索、筛选。
2. 邮件或机器人推送。
3. 股票历史数据缓存。
4. 多数据源切换。
5. 板块维度统计。

### V3 高级监控

1. 首次突破均线提醒。
2. 多头 / 空头排列变化提醒。
3. 连续站上 / 跌破均线天数。
4. 可视化走势图。
5. Web 服务化部署。
