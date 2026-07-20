# A股研究工具箱 API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

本地 SQLite 数据库默认写入仓库根目录的 `data/stock-flow.db`。

主要能力模块：

- `app.modules.money_flow`：个股与板块历史资金流。
- `app.modules.stock_move_attribution`：最新交易日涨跌归因。
- `app.infrastructure.eastmoney`：两项能力共享的东方财富传输基础设施。
