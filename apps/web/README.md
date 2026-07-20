# A股研究工具箱 Web

```bash
cd apps/web
npm install
npm run dev
```

默认调用 `http://localhost:8000`。如需修改后端地址：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

页面入口：

- `/money-flow`：资金流透镜。
- `/attribution`：股票涨跌归因。
- `/`：重定向到 `/money-flow`。
