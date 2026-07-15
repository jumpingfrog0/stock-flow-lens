"use client";

import { Plus, Search, X } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ApiError, searchBoards } from "@/lib/api";
import type { BoardSearchItem, BoardType, DataSource } from "@/types/money-flow";

type BoardQueryPanelProps = {
  source: DataSource;
  type: BoardType;
  startDate: string;
  endDate: string;
  isLoading: boolean;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onSubmit: (boards: string[], startDate: string, endDate: string, type: BoardType) => void;
};

export function BoardQueryPanel({
  source,
  type,
  startDate,
  endDate,
  isLoading,
  onStartDateChange,
  onEndDateChange,
  onSubmit,
}: BoardQueryPanelProps) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<BoardSearchItem[]>([]);
  const [selectedBoards, setSelectedBoards] = useState<BoardSearchItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQuery("");
    setSuggestions([]);
    setSelectedBoards([]);
    setError(null);
  }, [source, type]);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setSuggestions([]);
      setIsSearching(false);
      setError(null);
      return;
    }

    let isActive = true;
    setIsSearching(true);
    const timer = window.setTimeout(() => {
      searchBoards({ type, source, q: trimmed, limit: 10 })
        .then((items) => {
          if (isActive) {
            setSuggestions(items);
            setError(null);
          }
        })
        .catch((err) => {
          if (isActive) {
            setSuggestions([]);
            setError(err instanceof ApiError ? err.message : "板块搜索失败");
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
  }, [query, source, type]);

  function addBoard(board: BoardSearchItem) {
    setSelectedBoards((current) => {
      if (current.some((item) => item.code === board.code)) {
        return current;
      }
      return [...current, board];
    });
    setQuery("");
    setSuggestions([]);
  }

  function removeBoard(code: string) {
    setSelectedBoards((current) => current.filter((item) => item.code !== code));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(
      selectedBoards.map((item) => item.code),
      startDate,
      endDate,
      type,
    );
  }

  const label = type === "industry" ? "行业" : "概念";

  return (
    <form onSubmit={handleSubmit} className="rounded border border-border bg-panel p-4 shadow-surface">
      <div className="grid gap-4 lg:grid-cols-[1fr_160px_160px_auto] lg:items-end">
        <div className="relative">
          <span className="text-sm font-medium text-ink">{label}板块</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="mt-2 h-10 w-full rounded border border-border bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
            placeholder={`搜索${label}名称或代码`}
          />
          {query.trim() ? (
            <div className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded border border-border bg-white shadow-lg">
              {isSearching ? <div className="px-3 py-2 text-sm text-muted">搜索中...</div> : null}
              {!isSearching && suggestions.length === 0 ? (
                <div className="px-3 py-2 text-sm text-muted">无匹配板块</div>
              ) : null}
              {suggestions.map((board) => (
                <button
                  key={board.code}
                  type="button"
                  onClick={() => addBoard(board)}
                  className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition hover:bg-blue-50"
                >
                  <span className="font-medium text-ink">{board.name}</span>
                  <span className="shrink-0 text-xs text-muted">{board.code}</span>
                </button>
              ))}
            </div>
          ) : null}
          {error ? <div className="mt-2 text-xs text-negative">{error}</div> : null}
        </div>

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
          disabled={isLoading || selectedBoards.length === 0}
          className="inline-flex h-10 items-center justify-center gap-2 rounded bg-accent px-4 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          title={`查询${label}资金流`}
        >
          <Search className="h-4 w-4" aria-hidden="true" />
          {isLoading ? "查询中" : "查询"}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {selectedBoards.length === 0 ? (
          <span className="text-xs text-muted">从搜索结果添加一个或多个{label}板块。</span>
        ) : null}
        {selectedBoards.map((board) => (
          <span
            key={board.code}
            className="inline-flex items-center gap-2 rounded border border-border bg-white px-2 py-1 text-sm text-ink"
          >
            <Plus className="h-3.5 w-3.5 text-muted" aria-hidden="true" />
            {board.name}
            <span className="text-xs text-muted">{board.code}</span>
            <button
              type="button"
              onClick={() => removeBoard(board.code)}
              className="text-muted transition hover:text-negative"
              title="移除"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </span>
        ))}
      </div>
    </form>
  );
}
