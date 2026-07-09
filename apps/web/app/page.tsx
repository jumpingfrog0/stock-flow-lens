"use client";

import { useMemo, useState } from "react";

import { CumulativeLineChart } from "@/components/cumulative-line-chart";
import { DailyDetailTable } from "@/components/daily-detail-table";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { MoneyFlowBarChart } from "@/components/money-flow-bar-chart";
import { QueryForm } from "@/components/query-form";
import { SummaryTable } from "@/components/summary-table";
import { ApiError, fetchMoneyFlowSummary } from "@/lib/api";
import { exportMoneyFlowCsv } from "@/lib/csv";
import { defaultDateRange, directionClass, directionLabel, formatAmount } from "@/lib/format";
import type { MoneyFlowSummaryResponse } from "@/types/money-flow";

export default function HomePage() {
  const initialRange = useMemo(() => defaultDateRange(), []);
  const [data, setData] = useState<MoneyFlowSummaryResponse | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedItem = data?.items.find((item) => item.code === selectedCode) ?? data?.items[0] ?? null;

  async function handleSubmit(symbols: string[], startDate: string, endDate: string) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchMoneyFlowSummary({
        symbols,
        startDate,
        endDate,
        source: "eastmoney",
      });
      setData(response);
      setSelectedCode(response.items[0]?.code ?? null);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "查询失败，请稍后重试";
      setData(null);
      setSelectedCode(null);
      setError(message);
    } finally {
      setIsLoading(false);
    }
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

        <QueryForm
          initialStartDate={initialRange.startDate}
          initialEndDate={initialRange.endDate}
          isLoading={isLoading}
          canExport={Boolean(data?.items.length)}
          onSubmit={handleSubmit}
          onExport={() => {
            if (data) {
              exportMoneyFlowCsv(data);
            }
          }}
        />

        {error ? <ErrorState message={error} /> : null}

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
