import type { Metadata } from "next";

import { AppShell } from "@/components/app-shell";
import { StockAttributionWorkspace } from "@/components/stock-attribution-workspace";

export const metadata: Metadata = {
  title: "股票涨跌归因",
  description: "基于市场、风格、行业、个股与公告证据分析最新交易日的股票涨跌",
};

type Props = {
  searchParams?: { symbol?: string | string[] };
};

export default function AttributionPage({ searchParams }: Props) {
  const symbolParam = searchParams?.symbol;
  const initialSymbol = Array.isArray(symbolParam) ? symbolParam[0] : symbolParam || "";

  return (
    <AppShell active="attribution">
      <div className="flex w-full flex-col gap-5">
        <header>
          <h1 className="text-2xl font-semibold text-ink md:text-3xl">股票涨跌归因</h1>
          <p className="mt-1 text-sm text-muted">
            独立分析最新交易日的市场风格、行业共振、个股交易结构与公告证据。
          </p>
        </header>
        <StockAttributionWorkspace initialSymbol={initialSymbol} />
      </div>
    </AppShell>
  );
}
