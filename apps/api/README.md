# 资金流透镜 API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

本地 SQLite 数据库默认写入仓库根目录的 `data/stock-flow.db`。
