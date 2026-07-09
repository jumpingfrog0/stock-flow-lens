"use client";

import ReactECharts from "echarts-for-react";
import type { MoneyFlowItem } from "@/types/money-flow";
import { formatAmount } from "@/lib/format";

type MoneyFlowBarChartProps = {
  item: MoneyFlowItem;
};

export function MoneyFlowBarChart({ item }: MoneyFlowBarChartProps) {
  const option = {
    animation: false,
    grid: { left: 64, right: 24, top: 32, bottom: 48 },
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number) => formatAmount(value),
    },
    xAxis: {
      type: "category",
      data: item.daily.map((row) => row.tradeDate),
      axisLabel: { color: "#65758b" },
      axisLine: { lineStyle: { color: "#d8dde6" } },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: "#65758b",
        formatter: (value: number) => formatAmount(value).replace(" ", ""),
      },
      splitLine: { lineStyle: { color: "#e9edf3" } },
    },
    series: [
      {
        type: "bar",
        name: "主力净流入",
        data: item.daily.map((row) => row.mainNetInflow),
        itemStyle: {
          color: (params: { value: number }) => (params.value >= 0 ? "#178f5d" : "#c2413b"),
        },
      },
    ],
  };

  return (
    <section className="rounded border border-border bg-panel p-4 shadow-surface">
      <h2 className="text-base font-semibold text-ink">每日资金流</h2>
      <ReactECharts option={option} style={{ height: 320, width: "100%" }} />
    </section>
  );
}
