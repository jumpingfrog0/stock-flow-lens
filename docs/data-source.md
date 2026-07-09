# 东方财富数据源说明

1A 只实现东方财富个股资金流日线接口。

```text
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get
```

请求参数：

```text
secid={market}.{code}
lmt=0
klt=101
fields1=f1,f2,f3,f7
fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63
```

请求头：

```text
User-Agent: Mozilla/5.0
Referer: https://quote.eastmoney.com/
```

请求失败时，同一组参数最多重试 3 次。

`secid` 推导：

```text
600/601/603/605/688 -> 1.{code}
000/001/002/003/300/301 -> 0.{code}
```

字段映射：

```text
f51 -> tradeDate
f52 -> mainNetInflow
f53 -> smallInflow
f54 -> superLargeInflow
f55 -> largeInflow
f56 -> mediumInflow
f62 -> closePrice
f63 -> changePct
```

后端统一输出标准字段，前端不直接依赖东方财富字段名。

缓存说明：

```text
API 对外数据源和 SQLite 缓存 source 均为 eastmoney。
```
