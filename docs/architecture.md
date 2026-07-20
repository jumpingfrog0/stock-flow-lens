# A股研究工具箱架构

## 产品边界

- `/money-flow` 回答“指定区间内资金如何流动”，负责查询、缓存、统计、图表和导出。
- `/attribution` 回答“股票最新交易日为什么涨跌”，负责证据采集、规则归因和反事实检验。
- 资金流结果可以携带 `symbol` 跳转到归因页面，但两个页面不共享业务状态。

## 模块化单体

前端继续使用一个 Next.js 应用，后端继续使用一个 FastAPI 进程：

```text
apps/web/app/money-flow           资金流页面
apps/web/app/attribution          归因页面

apps/api/app/modules/money_flow
  routes / board_routes           HTTP 入口
  service / board_service         区间资金流用例
  schemas / board_schemas         模块契约

apps/api/app/modules/stock_move_attribution
  routes                          HTTP 入口
  service                         股票解析与用例编排
  evidence                        市场证据采集
  engine                          纯规则归因
  schemas                         模块契约

apps/api/app/infrastructure/eastmoney
  client                          共享请求、重试、域名与传输降级
```

## 依赖规则

- 资金流模块和归因模块不得互相调用。
- 两个模块可以依赖股票目录、证券标识和外部数据源等中性能力。
- 归因引擎不访问数据库或网络，只接收证据并返回确定性判断。
- 后端归因引擎是阈值、评分和置信度的唯一事实源。
- Web 与仓库内 Skill 均通过 `POST /api/stock-move/attribution` 使用归因能力。
