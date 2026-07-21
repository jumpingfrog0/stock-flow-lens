#!/bin/zsh

# 在终端中运行此文件即可启动前后端服务。
set -u

PROJECT_DIR="${0:A:h}"
API_DIR="$PROJECT_DIR/apps/api"
WEB_DIR="$PROJECT_DIR/apps/web"
API_PORT=8000
WEB_PORT=3000
API_PID=""
WEB_PID=""
STOPPING=0

cleanup() {
  (( STOPPING )) && return
  STOPPING=1
  trap - INT TERM

  print "\n正在停止服务…"
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "$WEB_PID" ]] && kill "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true
  [[ -n "$WEB_PID" ]] && wait "$WEB_PID" 2>/dev/null || true
  print "服务已停止。"
}

port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

if ! command -v python3 >/dev/null 2>&1; then
  print "未找到 Python 3，请先安装 Python 3 后重试。"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  print "未找到 npm，请先安装 Node.js（含 npm）后重试。"
  exit 1
fi

if port_in_use "$API_PORT" || port_in_use "$WEB_PORT"; then
  print "端口 $API_PORT 或 $WEB_PORT 已被占用。请先关闭已有服务后再启动。"
  exit 1
fi

if [[ ! -d "$API_DIR/.venv" ]]; then
  print "正在创建后端 Python 环境…"
  python3 -m venv "$API_DIR/.venv" || exit 1
fi

if [[ ! -f "$API_DIR/.venv/.dependencies-installed" || "$API_DIR/requirements.txt" -nt "$API_DIR/.venv/.dependencies-installed" ]]; then
  print "正在安装后端依赖（首次启动需要联网）…"
  "$API_DIR/.venv/bin/python" -m pip install -r "$API_DIR/requirements.txt" || exit 1
  touch "$API_DIR/.venv/.dependencies-installed"
fi

if [[ ! -d "$WEB_DIR/node_modules" ]]; then
  print "正在安装前端依赖（首次启动需要联网）…"
  (cd "$WEB_DIR" && npm install) || exit 1
fi

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM
trap cleanup EXIT

print "正在启动后端：http://localhost:$API_PORT"
(cd "$API_DIR" && exec .venv/bin/python -m uvicorn app.main:app --reload --port "$API_PORT") &
API_PID=$!

print "正在启动前端：http://localhost:$WEB_PORT"
(cd "$WEB_DIR" && exec ./node_modules/.bin/next dev) &
WEB_PID=$!

print "\n服务启动中，浏览器将在后端就绪后打开。"
for _ in {1..30}; do
  if curl --fail --silent http://localhost:"$API_PORT"/health >/dev/null 2>&1 && \
    curl --fail --silent http://localhost:"$WEB_PORT" >/dev/null 2>&1; then
    open http://localhost:"$WEB_PORT"
    print "已打开 http://localhost:$WEB_PORT"
    print "保持此窗口打开；按 Ctrl+C 可停止两个服务。"
    wait "$API_PID"
    exit $?
  fi
  sleep 1
done

print "后端在 30 秒内未就绪，请查看上方日志。"
exit 1
