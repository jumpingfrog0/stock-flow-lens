# AGENTS.md

## 项目概况

`stock-flow-lens` 是本地部署的 A 股资金流统计工具。

- 后端：`apps/api`，FastAPI + SQLite。
- 前端：`apps/web`，Next.js + TypeScript + Tailwind + ECharts。
- 数据缓存默认写入：`data/stock-flow.db`。

## 常用命令

后端：

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest
```

前端：

```bash
cd apps/web
npm install
npm run dev
npm run lint
npm run typecheck
npm run build
```

## 开发约定

- 优先保持改动小而聚焦，不做无关重构。
- 修改后端逻辑时，补充或更新 `apps/api/tests` 下的测试。
- 修改前端类型、接口或页面数据结构时，运行 `npm run typecheck`。
- 前后端接口变更时，同步更新 `docs/api.md` 和相关类型定义。
- 不提交本地运行产物、虚拟环境、缓存数据库或构建输出。
- Git commit 信息使用中文，简洁说明本次变更。
- 需要写入 `.git` 的操作（如 `git add`、`git commit`、`git commit --amend`）直接申请提升权限执行，避免因沙箱写入限制先失败一次。

## 代码风格

- Python 代码保持简单直白，业务逻辑优先放在 `services`，路由层只做参数和响应组织。
- TypeScript 组件优先复用现有组件与类型，避免引入新的状态管理或 UI 框架。
- 面向用户的错误信息要具体、可行动；日志和异常不要吞掉原始原因。
