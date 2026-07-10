"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { BoardQueryPanel } from "@/components/board-query-panel";
import { CumulativeLineChart } from "@/components/cumulative-line-chart";
import { DailyDetailTable } from "@/components/daily-detail-table";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { MoneyFlowBarChart } from "@/components/money-flow-bar-chart";
import { QueryForm } from "@/components/query-form";
import { QueryHistoryPanel } from "@/components/query-history-panel";
import { SummaryTable } from "@/components/summary-table";
import { WatchlistPanel } from "@/components/watchlist-panel";
import {
  addWatchlistItem,
  ApiError,
  createQueryHistory,
  createWatchlist,
  deleteWatchlist,
  deleteWatchlistItem,
  fetchBoardFlowSummary,
  fetchMoneyFlowSummary,
  fetchQueryHistory,
  fetchWatchlists,
  refreshRecentMoneyFlow,
  updateWatchlist,
} from "@/lib/api";
import { exportMoneyFlowCsv } from "@/lib/csv";
import { exportMoneyFlowExcel } from "@/lib/excel";
import { defaultDateRange, directionClass, directionLabel, formatAmount } from "@/lib/format";
import type { BoardType, MoneyFlowSummaryResponse, QueryHistoryItem, Watchlist } from "@/types/money-flow";

type WorkspaceMode = "stock" | BoardType;

type StockQuery = {
  symbols: string[];
  startDate: string;
  endDate: string;
};

const TABS: { value: WorkspaceMode; label: string }[] = [
  { value: "stock", label: "个股" },
  { value: "industry", label: "行业" },
  { value: "concept", label: "概念" },
];

export default function HomePage() {
  const initialRange = useMemo(() => defaultDateRange(), []);
  const [mode, setMode] = useState<WorkspaceMode>("stock");
  const [resultMode, setResultMode] = useState<WorkspaceMode>("stock");
  const [rawSymbols, setRawSymbols] = useState("300308, 300502, 603986");
  const [startDate, setStartDate] = useState(initialRange.startDate);
  const [endDate, setEndDate] = useState(initialRange.endDate);
  const [data, setData] = useState<MoneyFlowSummaryResponse | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshingRecent, setIsRefreshingRecent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sideError, setSideError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isWatchlistsLoading, setIsWatchlistsLoading] = useState(false);
  const [lastStockQuery, setLastStockQuery] = useState<StockQuery | null>(null);

  const selectedItem = data?.items.find((item) => item.code === selectedCode) ?? data?.items[0] ?? null;
  const resultLabel = TABS.find((tab) => tab.value === resultMode)?.label ?? "个股";

  const loadHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const items = await fetchQueryHistory(8);
      setHistory(items);
    } catch (err) {
      setSideError(errorMessage(err, "查询历史加载失败"));
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  const loadWatchlists = useCallback(async () => {
    setIsWatchlistsLoading(true);
    try {
      const items = await fetchWatchlists();
      setWatchlists(items);
    } catch (err) {
      setSideError(errorMessage(err, "自选分组加载失败"));
    } finally {
      setIsWatchlistsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
    void loadWatchlists();
  }, [loadHistory, loadWatchlists]);

  async function handleStockSubmit(
    symbols: string[],
    queryStartDate: string,
    queryEndDate: string,
    options: { saveHistory?: boolean } = {},
  ) {
    setIsLoading(true);
    setError(null);
    setSideError(null);
    try {
      const response = await fetchMoneyFlowSummary({
        symbols,
        startDate: queryStartDate,
        endDate: queryEndDate,
        source: "eastmoney",
      });
      setData(response);
      setSelectedCode(response.items[0]?.code ?? null);
      setResultMode("stock");
      setLastStockQuery({ symbols, startDate: queryStartDate, endDate: queryEndDate });
      if (options.saveHistory !== false) {
        try {
          await createQueryHistory({
            symbols,
            startDate: queryStartDate,
            endDate: queryEndDate,
            source: "eastmoney",
          });
          void loadHistory();
        } catch (err) {
          setSideError(errorMessage(err, "查询成功，但历史保存失败"));
        }
      }
    } catch (err) {
      setData(null);
      setSelectedCode(null);
      setError(errorMessage(err, "查询失败，请稍后重试"));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleBoardSubmit(
    boards: string[],
    queryStartDate: string,
    queryEndDate: string,
    type: BoardType,
  ) {
    setIsLoading(true);
    setError(null);
    setSideError(null);
    try {
      const response = await fetchBoardFlowSummary({
        boards,
        startDate: queryStartDate,
        endDate: queryEndDate,
        type,
        source: "eastmoney",
      });
      setData(response);
      setSelectedCode(response.items[0]?.code ?? null);
      setResultMode(type);
    } catch (err) {
      setData(null);
      setSelectedCode(null);
      setError(errorMessage(err, "板块资金流查询失败"));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRefreshRecent() {
    if (!lastStockQuery || resultMode !== "stock") {
      return;
    }
    setIsRefreshingRecent(true);
    setError(null);
    setSideError(null);
    try {
      await refreshRecentMoneyFlow({ symbols: lastStockQuery.symbols, source: "eastmoney" });
      await handleStockSubmit(lastStockQuery.symbols, lastStockQuery.startDate, lastStockQuery.endDate, {
        saveHistory: false,
      });
    } catch (err) {
      setError(errorMessage(err, "最近交易日刷新失败"));
    } finally {
      setIsRefreshingRecent(false);
    }
  }

  function handleReuseHistory(item: QueryHistoryItem) {
    setMode("stock");
    setRawSymbols(item.symbols.join("\n"));
    setStartDate(item.startDate);
    setEndDate(item.endDate);
    void handleStockSubmit(item.symbols, item.startDate, item.endDate, { saveHistory: false });
  }

  async function handleCreateWatchlist(name: string) {
    try {
      await createWatchlist(name);
      await loadWatchlists();
    } catch (err) {
      setSideError(errorMessage(err, "自选分组创建失败"));
    }
  }

  async function handleRenameWatchlist(id: number, name: string) {
    try {
      await updateWatchlist(id, name);
      await loadWatchlists();
    } catch (err) {
      setSideError(errorMessage(err, "自选分组重命名失败"));
    }
  }

  async function handleDeleteWatchlist(id: number) {
    try {
      await deleteWatchlist(id);
      await loadWatchlists();
    } catch (err) {
      setSideError(errorMessage(err, "自选分组删除失败"));
    }
  }

  async function handleAddWatchlistItem(id: number, symbol: string) {
    try {
      await addWatchlistItem(id, symbol);
      await loadWatchlists();
    } catch (err) {
      setSideError(errorMessage(err, "添加自选股失败"));
    }
  }

  async function handleRemoveWatchlistItem(id: number, symbol: string) {
    try {
      await deleteWatchlistItem(id, symbol);
      await loadWatchlists();
    } catch (err) {
      setSideError(errorMessage(err, "移除自选股失败"));
    }
  }

  function handleWatchlistQuery(symbols: string[]) {
    setMode("stock");
    setRawSymbols(symbols.join("\n"));
    void handleStockSubmit(symbols, startDate, endDate);
  }

  return (
    <main className="min-h-screen bg-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-6 md:px-6">
        <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-ink md:text-3xl">资金流透镜</h1>
            <p className="mt-1 text-sm text-muted">A 股主力资金流统计、本地缓存与可视化</p>
          </div>
          {data ? (
            <div className="rounded border border-border bg-white px-4 py-3 text-right shadow-surface">
              <div className="text-xs text-muted">多股票合计</div>
              <div className={`mt-1 text-lg font-semibold ${directionClass(data.totalDirection)}`}>
                {formatAmount(data.totalMainNetInflow)}
              </div>
              <div className={`text-xs ${directionClass(data.totalDirection)}`}>
                {directionLabel(data.totalDirection, data.totalDirectionAmount)}
              </div>
            </div>
          ) : null}
        </header>

        <div className="flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setMode(tab.value)}
              className={`h-9 rounded border px-4 text-sm font-medium transition ${
                mode === tab.value
                  ? "border-accent bg-accent text-white"
                  : "border-border bg-white text-ink hover:bg-slate-50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {mode === "stock" ? (
          <QueryForm
            rawSymbols={rawSymbols}
            startDate={startDate}
            endDate={endDate}
            isLoading={isLoading}
            isRefreshingRecent={isRefreshingRecent}
            canExport={Boolean(data?.items.length)}
            canRefreshRecent={Boolean(lastStockQuery && data?.items.length && resultMode === "stock")}
            onRawSymbolsChange={setRawSymbols}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
            onSubmit={handleStockSubmit}
            onRefreshRecent={handleRefreshRecent}
            onExportCsv={() => {
              if (data) {
                exportMoneyFlowCsv(data);
              }
            }}
            onExportExcel={() => {
              if (data) {
                exportMoneyFlowExcel(data);
              }
            }}
          />
        ) : (
          <BoardQueryPanel
            type={mode}
            startDate={startDate}
            endDate={endDate}
            isLoading={isLoading}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
            onSubmit={handleBoardSubmit}
          />
        )}

        <div className="grid gap-5 xl:grid-cols-[minmax(280px,0.75fr)_minmax(0,1.25fr)]">
          <QueryHistoryPanel items={history} isLoading={isHistoryLoading} onReuse={handleReuseHistory} />
          <WatchlistPanel
            watchlists={watchlists}
            isLoading={isWatchlistsLoading}
            onCreate={handleCreateWatchlist}
            onRename={handleRenameWatchlist}
            onDelete={handleDeleteWatchlist}
            onAddItem={handleAddWatchlistItem}
            onRemoveItem={handleRemoveWatchlistItem}
            onQuery={handleWatchlistQuery}
          />
        </div>

        {error ? <ErrorState message={error} /> : null}
        {sideError ? <ErrorState title="辅助操作失败" message={sideError} /> : null}

        {data?.errors.length ? (
          <ErrorState
            title="部分股票查询失败"
            message={data.errors
              .map((item) => `${item.code ?? "-"}：${item.message}（${item.errorCode}）`)
              .join("；")}
          />
        ) : null}

        {!data && !error ? <EmptyState /> : null}
        {data && data.items.length === 0 ? (
          <EmptyState title="区间无数据" message="当前条件没有返回可展示的资金流数据。" />
        ) : null}

        {data && selectedItem ? (
          <>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-ink">{resultLabel}查询结果</h2>
              <div className="text-xs text-muted">
                {data.range.startDate} 至 {data.range.endDate}
              </div>
            </div>
            <SummaryTable
              items={data.items}
              selectedCode={selectedItem.code}
              onSelect={(code) => setSelectedCode(code)}
            />
            <div className="grid gap-5 xl:grid-cols-2">
              <MoneyFlowBarChart item={selectedItem} />
              <CumulativeLineChart item={selectedItem} />
            </div>
            <DailyDetailTable item={selectedItem} />
          </>
        ) : null}
      </div>
    </main>
  );
}

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}
