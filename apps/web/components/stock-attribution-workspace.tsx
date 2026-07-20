"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { StockMoveAttributionPanel } from "@/components/stock-move-attribution-panel";
import { ApiError, fetchStockMoveAttribution } from "@/lib/api";
import type { StockMoveAttributionResponse } from "@/types/stock-move-attribution";

type Props = {
  initialSymbol: string;
};

export function StockAttributionWorkspace({ initialSymbol }: Props) {
  const router = useRouter();
  const [symbol, setSymbol] = useState(initialSymbol);
  const [data, setData] = useState<StockMoveAttributionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    const cleaned = symbol.trim();
    if (!cleaned) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchStockMoveAttribution(cleaned);
      setData(result);
      setSymbol(result.stock.code);
      router.replace(`/attribution?symbol=${encodeURIComponent(result.stock.code)}`, {
        scroll: false,
      });
    } catch (err) {
      setData(null);
      setError(errorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <StockMoveAttributionPanel
      symbol={symbol}
      data={data}
      isLoading={isLoading}
      error={error}
      onSymbolChange={(value) => {
        setSymbol(value);
        setData(null);
        setError(null);
      }}
      onAnalyze={handleAnalyze}
    />
  );
}

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : "股票涨跌归因失败，请稍后重试";
}
