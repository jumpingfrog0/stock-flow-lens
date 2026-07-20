# A股研究工具箱

`A股研究工具箱` 是本地部署的个人 A 股研究应用，目前包含两个相互独立的工具：

- `资金流透镜`：查询股票或板块的区间资金流，提供缓存、统计、图表和导出。
- `股票涨跌归因`：分析最新交易日的市场、风格、行业、个股和公告证据，并执行规则评分与反事实检验。

两个工具运行在同一套 Next.js + FastAPI 模块化单体中，只共享股票标识和数据源基础设施，不共享业务状态。

## 本地启动

### 一键启动

在仓库根目录的终端中执行：

```bash
./start.sh
```

首次运行会自动创建 Python 虚拟环境和安装前后端依赖，随后会打开 `http://localhost:3000`。保持终端窗口打开；按 `Ctrl+C` 可停止两个服务。

### 分别启动

启动后端：

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

启动前端：

```bash
cd apps/web
npm install
npm run dev
```

访问：

```text
资金流透镜：http://localhost:3000/money-flow
股票涨跌归因：http://localhost:3000/attribution
```

访问根路径 `http://localhost:3000` 会自动进入资金流透镜。

前端默认请求：

```text
http://localhost:8000
```

如需修改：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 资金流透镜

- 输入单只或多只 6 位 A 股代码。
- 选择开始日期和结束日期。
- 调用东方财富个股资金流日线接口。
- SQLite 缓存每日资金流数据。
- 查询时优先读取 SQLite，缓存为空时请求东方财富。
- 返回区间主力净流入、净流出方向、每日明细。
- 展示统计表、每日资金流柱状图、累计净流入折线图。
- 支持 CSV 导出。
- 显示股票不存在、接口失败、区间无数据等基础错误。

## 股票涨跌归因

- 可直接输入股票代码或本地股票库可解析的名称，不依赖资金流查询结果。
- 读取最新股票行情、主要指数、全市场涨跌家数、所属行业、同行表现、资金流和公司公告。
- 返回一级驱动、置信度、三类驱动评分、反事实检查和数据限制。
- API 响应携带 `methodologyVersion`；后端规则引擎是评分阈值的唯一事实源。
- 仓库内 `skills/analyze-stock-move` 通过归因 API 组织证据并在必要时补充权威新闻。

## 资金流验收

推荐使用：

```text
300308, 300502, 603986
```

验收项：

- 可以查询自定义日期区间。
- 结果包含每只股票区间主力净流入。
- 结果包含多只股票合计主力净流入。
- 负值明确显示净流出。
- 每日资金流柱状图和累计净流入折线图正常显示。
- CSV 可以导出。
- 首次成功查询后 `data/stock-flow.db` 写入缓存。
- 第二次同股票同区间查询优先读取缓存。

## 后端测试

```bash
cd apps/api
pytest
```
