#!/usr/bin/env python3
import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="调用 stock-flow-lens 股票涨跌归因接口")
    parser.add_argument("symbol", help="6 位 A 股代码或本地股票库可解析的名称")
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="stock-flow-lens API 地址，默认 http://127.0.0.1:8000",
    )
    parser.add_argument("--timeout", type=float, default=45.0, help="请求超时秒数")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    url = f"{args.api_base.rstrip('/')}/api/stock-analysis/attribution"
    payload = json.dumps({"symbol": args.symbol}, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=args.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"归因接口返回 HTTP {exc.code}: {detail}", file=sys.stderr)
        return 2
    except URLError as exc:
        print(
            f"无法连接 {args.api_base}：{exc.reason}。请先启动 stock-flow-lens 后端。",
            file=sys.stderr,
        )
        return 3
    except (TimeoutError, json.JSONDecodeError) as exc:
        print(f"归因接口响应不可用：{exc}", file=sys.stderr)
        return 4

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
