import type {
  BoardFlowSummaryRequest,
  BoardFlowSummaryResponse,
  BoardSearchItem,
  BoardType,
  MoneyFlowSummaryRequest,
  MoneyFlowSummaryResponse,
  MoneyFlowRefreshRecentRequest,
  MoneyFlowRefreshRecentResponse,
  QueryHistoryCreateRequest,
  QueryHistoryItem,
  StockRefreshRequest,
  StockRefreshResponse,
  StockSearchItem,
  Watchlist,
} from "@/types/money-flow";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  errorCode?: string;

  constructor(message: string, status: number, errorCode?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

export async function fetchMoneyFlowSummary(
  request: MoneyFlowSummaryRequest,
): Promise<MoneyFlowSummaryResponse> {
  return fetchJson<MoneyFlowSummaryResponse>(`${API_BASE_URL}/api/money-flow/summary`, "查询失败", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}

export async function refreshRecentMoneyFlow(
  request: MoneyFlowRefreshRecentRequest,
): Promise<MoneyFlowRefreshRecentResponse> {
  return fetchJson<MoneyFlowRefreshRecentResponse>(
    `${API_BASE_URL}/api/money-flow/refresh-recent`,
    "最近交易日刷新失败",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );
}

export async function searchStocks(params: { q?: string; limit?: number }): Promise<StockSearchItem[]> {
  const searchParams = new URLSearchParams({
    q: params.q || "",
    limit: String(params.limit || 20),
  });
  return fetchJson<StockSearchItem[]>(
    `${API_BASE_URL}/api/stocks/search?${searchParams.toString()}`,
    "股票搜索失败",
  );
}

export async function refreshStocks(request: StockRefreshRequest = {}): Promise<StockRefreshResponse> {
  return fetchJson<StockRefreshResponse>(`${API_BASE_URL}/api/stocks/refresh`, "股票列表刷新失败", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}

export async function fetchQueryHistory(limit = 10): Promise<QueryHistoryItem[]> {
  const searchParams = new URLSearchParams({ limit: String(limit) });
  return fetchJson<QueryHistoryItem[]>(
    `${API_BASE_URL}/api/query-history?${searchParams.toString()}`,
    "查询历史加载失败",
  );
}

export async function createQueryHistory(
  request: QueryHistoryCreateRequest,
): Promise<QueryHistoryItem> {
  return fetchJson<QueryHistoryItem>(`${API_BASE_URL}/api/query-history`, "查询历史保存失败", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}

export async function fetchWatchlists(): Promise<Watchlist[]> {
  return fetchJson<Watchlist[]>(`${API_BASE_URL}/api/watchlists`, "自选分组加载失败");
}

export async function createWatchlist(name: string): Promise<Watchlist> {
  return fetchJson<Watchlist>(`${API_BASE_URL}/api/watchlists`, "自选分组创建失败", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });
}

export async function updateWatchlist(id: number, name: string): Promise<Watchlist> {
  return fetchJson<Watchlist>(`${API_BASE_URL}/api/watchlists/${id}`, "自选分组重命名失败", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });
}

export async function deleteWatchlist(id: number): Promise<void> {
  await fetchJson<void>(`${API_BASE_URL}/api/watchlists/${id}`, "自选分组删除失败", {
    method: "DELETE",
  });
}

export async function addWatchlistItem(id: number, symbol: string): Promise<Watchlist> {
  return fetchJson<Watchlist>(`${API_BASE_URL}/api/watchlists/${id}/items`, "添加自选股失败", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ symbol }),
  });
}

export async function deleteWatchlistItem(id: number, symbol: string): Promise<Watchlist> {
  return fetchJson<Watchlist>(
    `${API_BASE_URL}/api/watchlists/${id}/items/${encodeURIComponent(symbol)}`,
    "移除自选股失败",
    { method: "DELETE" },
  );
}

export async function searchBoards(params: {
  type: BoardType;
  q?: string;
  limit?: number;
}): Promise<BoardSearchItem[]> {
  const searchParams = new URLSearchParams({
    type: params.type,
    q: params.q || "",
    limit: String(params.limit || 20),
  });
  return fetchJson<BoardSearchItem[]>(
    `${API_BASE_URL}/api/boards/search?${searchParams.toString()}`,
    "板块搜索失败",
  );
}

export async function fetchBoardFlowSummary(
  request: BoardFlowSummaryRequest,
): Promise<BoardFlowSummaryResponse> {
  return fetchJson<BoardFlowSummaryResponse>(`${API_BASE_URL}/api/board-flow/summary`, "板块资金流查询失败", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
}

async function fetchJson<T>(url: string, fallbackMessage: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    await throwApiError(response, fallbackMessage);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

async function throwApiError(response: Response, fallbackMessage: string): Promise<never> {
  let message = fallbackMessage;
  let errorCode: string | undefined;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      message = body.detail;
    } else {
      message = body?.detail?.message || body?.message || message;
      errorCode = body?.detail?.errorCode || body?.errorCode;
    }
  } catch {
    message = response.statusText || message;
  }
  throw new ApiError(message, response.status, errorCode);
}
