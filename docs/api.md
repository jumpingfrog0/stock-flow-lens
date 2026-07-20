# A股研究工具箱 API

## GET /health

用于本地启动检查。

```json
{"status":"ok"}
```

## POST /api/money-flow/summary

1A 主接口，返回区间统计、每日明细和图表所需数据。`symbols` 支持 6 位股票代码或股票名称；名称解析规则为精确名称优先，否则唯一模糊匹配，多匹配返回 `AMBIGUOUS_SYMBOL`。

请求：

```json
{
  "source": "akshare",
  "symbols": ["300308", "300502", "603986"],
  "startDate": "2026-06-08",
  "endDate": "2026-07-07"
}
```

响应：

```json
{
  "source": "akshare",
  "range": {
    "startDate": "2026-06-08",
    "endDate": "2026-07-07"
  },
  "items": [
    {
      "code": "300308",
      "name": "中际旭创",
      "mainNetInflow": -21549000000,
      "direction": "outflow",
      "directionAmount": 21549000000,
      "tradeDays": 21,
      "daily": [
        {
          "tradeDate": "2026-06-08",
          "mainNetInflow": -120000000,
          "superLargeInflow": -50000000,
          "largeInflow": -70000000,
          "mediumInflow": 30000000,
          "smallInflow": 90000000,
          "closePrice": 100.25,
          "changePct": -1.23,
          "cumulativeMainNetInflow": -120000000
        }
      ]
    }
  ],
  "totalMainNetInflow": -21549000000,
  "totalDirection": "outflow",
  "totalDirectionAmount": 21549000000,
  "errors": []
}
```

成功查询会自动写入查询历史。

## POST /api/money-flow/refresh-recent

强制刷新指定股票最近 10 个自然日资金流，并覆盖本地缓存。`symbols` 支持股票代码或名称。

请求：

```json
{
  "source": "akshare",
  "symbols": ["300308", "中际旭创"]
}
```

响应：

```json
{
  "source": "akshare",
  "range": {
    "startDate": "2026-07-01",
    "endDate": "2026-07-10"
  },
  "items": [
    {
      "code": "300308",
      "name": "中际旭创",
      "refreshedRows": 7
    }
  ],
  "errors": []
}
```

## GET /api/stocks/search

搜索本地 `stocks` 表，支持代码和名称模糊匹配。

查询参数：

- `q`：搜索关键词，可为空。
- `limit`：返回数量，默认 `20`，最大 `100`。

响应：

```json
[
  {
    "code": "300308",
    "name": "中际旭创",
    "market": "sz",
    "secid": "0.300308",
    "industry": "通信设备",
    "updatedAt": "2026-07-10T00:00:00+00:00"
  }
]
```

## POST /api/stocks/refresh

从指定 provider 搜索或列表能力刷新股票基础信息并 upsert 到本地。默认使用 AKShare；EastMoney provider 当前未接入全市场列表，因此选择 `eastmoney` 时返回 `refreshed: 0`。

请求：

```json
{
  "query": "",
  "limit": 500,
  "source": "akshare"
}
```

响应：

```json
{
  "refreshed": 500
}
```

## GET /api/query-history

返回最近查询历史。

查询参数：

- `limit`：返回数量，默认 `50`，最大 `200`。

## POST /api/query-history

手动写入查询历史。

请求：

```json
{
  "symbols": ["300308"],
  "startDate": "2026-07-01",
  "endDate": "2026-07-10",
  "source": "akshare"
}
```

响应：

```json
{
  "id": 1,
  "symbols": ["300308"],
  "startDate": "2026-07-01",
  "endDate": "2026-07-10",
  "source": "akshare",
  "createdAt": "2026-07-10T00:00:00+00:00"
}
```

## /api/watchlists

自选股分组和分组股票管理。

- `GET /api/watchlists`：返回所有分组及 items。
- `POST /api/watchlists`：创建分组，请求 `{ "name": "重点观察" }`。
- `PATCH /api/watchlists/{id}`：重命名分组，请求 `{ "name": "短线观察" }`。
- `DELETE /api/watchlists/{id}`：删除分组。
- `POST /api/watchlists/{id}/items`：添加股票，请求 `{ "symbol": "中际旭创" }`。
- `DELETE /api/watchlists/{id}/items/{symbol}`：移除股票，`symbol` 支持代码或名称。

## GET /api/boards/search

搜索行业或概念板块。

查询参数：

- `type`：`industry` 或 `concept`。
- `q`：搜索关键词，可为空。
- `limit`：返回数量，默认 `20`，最大 `100`。
- `source`：`akshare` 或 `eastmoney`，默认 `akshare`。

示例：

```text
GET /api/boards/search?type=industry&q=半导体&limit=20&source=akshare
```

响应：

```json
[
  {
    "code": "BK0475",
    "name": "半导体",
    "type": "industry",
    "market": "board",
    "secid": "90.BK0475",
    "source": "akshare"
  }
]
```

## POST /api/board-flow/summary

1B 板块资金流汇总接口，响应结构复用个股资金流 summary，便于前端复用图表和表格。

请求：

```json
{
  "source": "akshare",
  "boards": ["BK0475", "BK0815"],
  "startDate": "2026-06-08",
  "endDate": "2026-07-07",
  "type": "industry"
}
```

响应：

```json
{
  "source": "akshare",
  "range": {
    "startDate": "2026-06-08",
    "endDate": "2026-07-07"
  },
  "items": [
    {
      "code": "BK0475",
      "name": "半导体",
      "mainNetInflow": 1250000000,
      "direction": "inflow",
      "directionAmount": 1250000000,
      "tradeDays": 21,
      "daily": [
        {
          "tradeDate": "2026-06-08",
          "mainNetInflow": 120000000,
          "superLargeInflow": 50000000,
          "largeInflow": 70000000,
          "mediumInflow": -30000000,
          "smallInflow": -90000000,
          "closePrice": 3210.55,
          "changePct": 1.23,
          "cumulativeMainNetInflow": 120000000
        }
      ]
    }
  ],
  "totalMainNetInflow": 1250000000,
  "totalDirection": "inflow",
  "totalDirectionAmount": 1250000000,
  "errors": []
}
```

## POST /api/stock-move/attribution

自动分析最新交易日的股票涨跌驱动。程序严格按全市场、风格、行业、个股和公告顺序收集证据，
并返回规则评分与反事实检验。该接口固定使用东方财富实时行情，不读取请求中的资金流 `source`。

请求：

```json
{
  "symbol": "002714"
}
```

核心响应：

```json
{
  "methodologyVersion": "1.0.0",
  "source": "eastmoney",
  "asOf": "2026-07-15",
  "primaryDriver": "market_rotation",
  "confidence": "high",
  "summary": "市场风格切换是一级驱动，行业共振与个股交易结构是放大因素。",
  "stock": {
    "code": "002714",
    "name": "牧原股份",
    "tradeDate": "2026-07-15",
    "industry": "养殖业",
    "styleBucket": "defensive_value",
    "closePrice": 39.65,
    "changePct": 4.12,
    "mainNetInflow": 225774032,
    "marketRelativePct": 5.09,
    "industryRelativePct": 2.77
  },
  "style": {
    "rotation": "high_to_low",
    "growthProxyChangePct": -2.73,
    "valueProxyChangePct": 0.095,
    "valueMinusGrowthPct": 2.825,
    "note": "成长代理指数走弱且价值代理显著占优，市场存在高低切换特征"
  },
  "drivers": [
    {
      "code": "market_rotation",
      "label": "市场风格切换",
      "score": 100,
      "evidence": ["价值与成长代理涨跌差达到 2.83 个百分点"],
      "limitations": []
    }
  ],
  "counterfactuals": [
    {
      "code": "same_day_announcement",
      "result": "weakens",
      "conclusion": "当日无新增公司公告，不应把旧公告当作直接催化"
    }
  ],
  "warnings": ["归因基于可观测行情和规则评分，不代表已知每笔交易的真实动机"]
}
```

`primaryDriver` 可能值：

```text
market_rotation
industry_move
stock_specific
mixed
insufficient
```

`methodologyVersion` 标识后端归因规则版本；后端引擎是评分阈值和置信度规则的唯一事实源。
评分用于比较三类解释的证据强弱，不是上涨概率或投资评级。实时资金流缺失且盘中资金流尚未
更新时，接口不会把上一交易日资金流用于当日归因，而会在 `warnings` 返回具体原因。

## 错误码

```text
INVALID_SYMBOL
AMBIGUOUS_SYMBOL
STOCK_NOT_FOUND
INVALID_SOURCE
WATCHLIST_NOT_FOUND
INVALID_BOARD
INVALID_DATE_RANGE
SOURCE_DATE_RANGE_UNSUPPORTED
NO_DATA
UPSTREAM_FAILED
PARTIAL_FAILED
```

HTTP 状态：

- `400`：参数、数据源或来源可用日期范围错误。
- `404`：单股票无数据。
- `502`：所选 provider 上游失败且无缓存。
- `200`：多股票部分成功，失败项放入 `errors`。
