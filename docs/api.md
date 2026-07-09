# 资金流透镜 API

## GET /health

用于本地启动检查。

```json
{"status":"ok"}
```

## POST /api/money-flow/summary

1A 主接口，返回区间统计、每日明细和图表所需数据。

请求：

```json
{
  "symbols": ["300308", "300502", "603986"],
  "startDate": "2026-06-08",
  "endDate": "2026-07-07",
  "source": "eastmoney"
}
```

响应：

```json
{
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

## 错误码

```text
INVALID_SYMBOL
INVALID_DATE_RANGE
NO_DATA
UPSTREAM_FAILED
PARTIAL_FAILED
```

HTTP 状态：

- `400`：参数错误。
- `404`：单股票无数据。
- `502`：东方财富失败且无缓存。
- `200`：多股票部分成功，失败项放入 `errors`。
