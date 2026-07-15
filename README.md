# 资金流透镜

`资金流透镜` 是本地部署的 A 股资金流统计网页版。1A 最小可用版实现股票代码输入、东方财富资金流拉取、SQLite 缓存、区间统计、表格/图表展示和 CSV 导出。

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
http://localhost:3000
```

前端默认请求：

```text
http://localhost:8000
```

如需修改：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 1A 功能

- 输入单只或多只 6 位 A 股代码。
- 选择开始日期和结束日期。
- 调用东方财富个股资金流日线接口。
- SQLite 缓存每日资金流数据。
- 查询时优先读取 SQLite，缓存为空时请求东方财富。
- 返回区间主力净流入、净流出方向、每日明细。
- 展示统计表、每日资金流柱状图、累计净流入折线图。
- 支持 CSV 导出。
- 显示股票不存在、接口失败、区间无数据等基础错误。

## 验收

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
