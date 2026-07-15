"use client";

import { Download, FileSpreadsheet, RefreshCw, Search } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError, refreshStocks, searchStocks } from "@/lib/api";
import type { DataSource, StockSearchItem } from "@/types/money-flow";

type QueryFormProps = {
  source: DataSource;
  rawSymbols: string;
  startDate: string;
  endDate: string;
  isLoading: boolean;
  isRefreshingRecent: boolean;
  canExport: boolean;
  canRefreshRecent: boolean;
  onRawSymbolsChange: (value: string) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onSubmit: (symbols: string[], startDate: string, endDate: string) => void;
  onExportCsv: () => void;
  onExportExcel: () => void;
  onRefreshRecent: () => void;
};

export function QueryForm({
  source,
  rawSymbols,
  startDate,
  endDate,
  isLoading,
  isRefreshingRecent,
  canExport,
  canRefreshRecent,
  onRawSymbolsChange,
  onStartDateChange,
  onEndDateChange,
  onSubmit,
  onExportCsv,
  onExportExcel,
  onRefreshRecent,
}: QueryFormProps) {
  const [stockQuery, setStockQuery] = useState("");
  const [suggestions, setSuggestions] = useState<StockSearchItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isRefreshingStocks, setIsRefreshingStocks] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const symbols = useMemo(() => parseSymbols(rawSymbols), [rawSymbols]);

  useEffect(() => {
    const query = stockQuery.trim();
    if (!query) {
      setSuggestions([]);
      setSearchError(null);
      setIsSearching(false);
      return;
    }

    let isActive = true;
    setIsSearching(true);
    const timer = window.setTimeout(() => {
      searchStocks({ q: query, limit: 8 })
        .then((items) => {
          if (isActive) {
            setSuggestions(items);
            setSearchError(null);
          }
        })
        .catch((err) => {
          if (isActive) {
            setSuggestions([]);
            setSearchError(err instanceof ApiError ? err.message : "股票搜索失败");
          }
        })
        .finally(() => {
          if (isActive) {
            setIsSearching(false);
          }
        });
    }, 220);

    return () => {
      isActive = false;
      window.clearTimeout(timer);
    };
  }, [stockQuery]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(symbols, startDate, endDate);
  }

  async function handleRefreshStocks() {
    setIsRefreshingStocks(true);
    setSearchError(null);
    try {
      await refreshStocks({ query: stockQuery.trim(), limit: 500, source });
      const items = await searchStocks({ q: stockQuery.trim(), limit: 8 });
      setSuggestions(items);
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : "股票列表刷新失败");
    } finally {
      setIsRefreshingStocks(false);
    }
  }

  function addStock(stock: StockSearchItem) {
    const next = appendToken(rawSymbols, stock.code);
    onRawSymbolsChange(next);
    setStockQuery("");
    setSuggestions([]);
  }

  return (
    <form onSubmit={handleSubmit} className="rounded border border-border bg-panel p-4 shadow-surface">
      <div className="grid gap-4 xl:grid-cols-[1fr_280px]">
        <label className="block">
          <span className="text-sm font-medium text-ink">股票代码或名称</span>
          <textarea
            value={rawSymbols}
            onChange={(event) => onRawSymbolsChange(event.target.value)}
            rows={3}
            className="mt-2 h-24 w-full resize-none rounded border border-border bg-white px-3 py-2 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
            placeholder="300308, 300502, 603986 或 平安银行"
          />
        </label>

        <div className="relative">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-medium text-ink">股票搜索</span>
            <button
              type="button"
              onClick={handleRefreshStocks}
              disabled={isRefreshingStocks}
              className="inline-flex h-7 items-center gap-1 rounded border border-border bg-white px-2 text-xs text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
              title="刷新本地股票列表"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefreshingStocks ? "animate-spin" : ""}`} />
              刷新
            </button>
          </div>
          <input
            value={stockQuery}
            onChange={(event) => setStockQuery(event.target.value)}
            className="mt-2 h-10 w-full rounded border border-border bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
            placeholder="输入代码或名称"
          />
          {stockQuery.trim() ? (
            <div className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded border border-border bg-white shadow-lg">
              {isSearching ? <div className="px-3 py-2 text-sm text-muted">搜索中...</div> : null}
              {!isSearching && suggestions.length === 0 ? (
                <div className="px-3 py-2 text-sm text-muted">无匹配股票</div>
              ) : null}
              {suggestions.map((stock) => (
                <button
                  key={stock.code}
                  type="button"
                  onClick={() => addStock(stock)}
                  className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition hover:bg-blue-50"
                >
                  <span className="min-w-0">
                    <span className="font-medium text-ink">{stock.name}</span>
                    <span className="ml-2 text-muted">{stock.code}</span>
                  </span>
                  <span className="shrink-0 text-xs text-muted">{stock.industry || stock.market}</span>
                </button>
              ))}
            </div>
          ) : null}
          {searchError ? <div className="mt-2 text-xs text-negative">{searchError}</div> : null}
        </div>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[160px_160px_auto_auto_auto_auto] lg:items-end">
        <label className="block">
          <span className="text-sm font-medium text-ink">开始日期</span>
          <input
            type="date"
            value={startDate}
            onChange={(event) => onStartDateChange(event.target.value)}
            className="mt-2 h-10 w-full rounded border border-border bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-ink">结束日期</span>
          <input
            type="date"
            value={endDate}
            onChange={(event) => onEndDateChange(event.target.value)}
            className="mt-2 h-10 w-full rounded border border-border bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <button
          type="submit"
          disabled={isLoading || symbols.length === 0}
          className="inline-flex h-10 items-center justify-center gap-2 rounded bg-accent px-4 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          title="查询资金流"
        >
          <Search className="h-4 w-4" aria-hidden="true" />
          {isLoading ? "查询中" : "查询"}
        </button>

        <button
          type="button"
          disabled={!canRefreshRecent || isRefreshingRecent}
          onClick={onRefreshRecent}
          className="inline-flex h-10 items-center justify-center gap-2 rounded border border-border bg-white px-4 text-sm font-medium text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          title="刷新最近交易日并重跑当前查询"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshingRecent ? "animate-spin" : ""}`} aria-hidden="true" />
          刷新近况
        </button>

        <button
          type="button"
          disabled={!canExport}
          onClick={onExportCsv}
          className="inline-flex h-10 items-center justify-center gap-2 rounded border border-border bg-white px-4 text-sm font-medium text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          title="导出 CSV"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          CSV
        </button>

        <button
          type="button"
          disabled={!canExport}
          onClick={onExportExcel}
          className="inline-flex h-10 items-center justify-center gap-2 rounded border border-border bg-white px-4 text-sm font-medium text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          title="导出 Excel"
        >
          <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
          Excel
        </button>
      </div>

      <div className="mt-3 text-xs text-muted">
        支持逗号、空格、换行分隔；当前有效关键词 {symbols.length} 个。
      </div>
    </form>
  );
}

function parseSymbols(input: string): string[] {
  const seen = new Set<string>();
  return input
    .split(/[,\s，]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => {
      if (seen.has(item)) {
        return false;
      }
      seen.add(item);
      return true;
    });
}

function appendToken(input: string, token: string): string {
  const tokens = parseSymbols(input);
  if (tokens.includes(token)) {
    return input;
  }
  return input.trim() ? `${input.trim()}\n${token}` : token;
}
