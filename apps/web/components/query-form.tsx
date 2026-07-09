"use client";

import { Download, Search } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

type QueryFormProps = {
  initialStartDate: string;
  initialEndDate: string;
  isLoading: boolean;
  canExport: boolean;
  onSubmit: (symbols: string[], startDate: string, endDate: string) => void;
  onExport: () => void;
};

export function QueryForm({
  initialStartDate,
  initialEndDate,
  isLoading,
  canExport,
  onSubmit,
  onExport,
}: QueryFormProps) {
  const [rawSymbols, setRawSymbols] = useState("300308, 300502, 603986");
  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
  const symbols = useMemo(() => parseSymbols(rawSymbols), [rawSymbols]);
  const hasInvalidTokens = rawSymbols.trim().length > 0 && symbols.length === 0;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(symbols, startDate, endDate);
  }

  return (
    <form onSubmit={handleSubmit} className="rounded border border-border bg-panel p-4 shadow-surface">
      <div className="grid gap-4 lg:grid-cols-[1fr_160px_160px_auto_auto] lg:items-end">
        <label className="block">
          <span className="text-sm font-medium text-ink">股票代码</span>
          <textarea
            value={rawSymbols}
            onChange={(event) => setRawSymbols(event.target.value)}
            rows={3}
            className="mt-2 h-24 w-full resize-none rounded border border-border bg-white px-3 py-2 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
            placeholder="300308, 300502, 603986"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-ink">开始日期</span>
          <input
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
            className="mt-2 h-10 w-full rounded border border-border bg-white px-3 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-blue-100"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-ink">结束日期</span>
          <input
            type="date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
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
          disabled={!canExport}
          onClick={onExport}
          className="inline-flex h-10 items-center justify-center gap-2 rounded border border-border bg-white px-4 text-sm font-medium text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
          title="导出 CSV"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          CSV
        </button>
      </div>

      <div className="mt-3 text-xs text-muted">
        支持逗号、空格、换行分隔；当前有效代码 {symbols.length} 个。
        {hasInvalidTokens ? <span className="ml-2 text-negative">请输入 6 位数字股票代码。</span> : null}
      </div>
    </form>
  );
}

function parseSymbols(input: string): string[] {
  const seen = new Set<string>();
  return input
    .split(/[,\s，]+/)
    .map((item) => item.trim())
    .filter((item) => /^\d{6}$/.test(item))
    .filter((item) => {
      if (seen.has(item)) {
        return false;
      }
      seen.add(item);
      return true;
    });
}
