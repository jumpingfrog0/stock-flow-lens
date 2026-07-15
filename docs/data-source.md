# 数据源说明

系统支持 `akshare` 和 `eastmoney` 两个数据源，默认使用 `akshare`。资金流缓存按
`stock_code + trade_date + source` 隔离，查询、手动刷新和自动刷新均不会混用数据。

## AKShare

依赖版本固定为 `akshare==1.18.64`。AKShare 接口为同步调用，后端在线程池中执行，
单次调用超时由 `STOCK_FLOW_AKSHARE_TIMEOUT_SECONDS` 控制，默认 20 秒，失败最多重试 3 次。

个股资金流使用：

```text
stock_individual_fund_flow
stock_individual_info_em
```

股票列表使用 `stock_info_a_code_name`，仅保留项目现有规则支持的沪深股票，暂不接入北交所。

板块能力使用：

```text
stock_board_industry_name_em
stock_board_concept_name_em
stock_sector_fund_flow_hist
stock_concept_fund_flow_hist
stock_board_industry_hist_em
stock_board_concept_hist_em
```

行业和概念资金流按日期与板块历史行情合并，以补充 `closePrice` 和 `changePct`；单个日期
未匹配行情时这两个字段为 `null`，行情接口整体失败时返回上游错误。

AKShare 资金流接口只返回上游当前可获得的近期数据，且没有历史翻页参数。请求开始日期早于
接口最早返回日期时，返回 `SOURCE_DATE_RANGE_UNSUPPORTED`，不会自动改用 EastMoney 补齐。
随着日常查询积累，已写入本地 AKShare 缓存的旧数据仍可继续查询。

AKShare 的上述资金流接口底层数据仍来自东方财富，因此它是独立 provider 适配层，不是独立行情上游。

## EastMoney 直连

个股和板块资金流日线使用：

```text
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get
```

板块搜索使用：

```text
https://push2.eastmoney.com/api/qt/clist/get
```

请求失败时，同一组参数最多重试 3 次。超时由
`STOCK_FLOW_EASTMONEY_TIMEOUT_SECONDS` 控制，默认 12 秒。

`secid` 推导：

```text
600/601/603/605/688 -> 1.{code}
000/001/002/003/300/301 -> 0.{code}
```

## 标准字段映射

两个 provider 均输出统一字段：

```text
tradeDate
mainNetInflow
superLargeInflow
largeInflow
mediumInflow
smallInflow
closePrice
changePct
```

前端不直接依赖 EastMoney 字段编号或 AKShare DataFrame 中文列名。汇总和最近刷新响应均返回
根级 `source`，CSV/Excel 导出也包含 `source` 列。
