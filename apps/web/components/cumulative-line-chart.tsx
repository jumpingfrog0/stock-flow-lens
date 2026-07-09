"use client";

import ReactECharts from "echarts-for-react";
import type { MoneyFlowItem } from "@/types/money-flow";
import { formatAmount } from "@/lib/format";

type CumulativeLineChartProps = {
  item: MoneyFlowItem;
};

export function CumulativeLineChart({ item }: CumulativeLineChartProps) {
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
        type: "line",
        name: "累计净流入",
        data: item.daily.map((row) => row.cumulativeMainNetInflow),
        smooth: true,
        symbolSize: 6,
        lineStyle: { color: "#2563eb", width: 2 },
        itemStyle: { color: "#2563eb" },
        areaStyle: { color: "rgba(37, 99, 235, 0.10)" },
      },
    ],
  };

  return (
    <section className="rounded border border-border bg-panel p-4 shadow-surface">
      <h2 className="text-base font-semibold text-ink">累计净流入</h2>
      <ReactECharts option={option} style={{ height: 320, width: "100%" }} />
    </section>
  );
}
