import type { MoneyFlowSummaryResponse } from "@/types/money-flow";

const COLUMNS = [
  "source",
  "code",
  "name",
  "tradeDate",
  "mainNetInflow",
  "superLargeInflow",
  "largeInflow",
  "mediumInflow",
  "smallInflow",
  "closePrice",
  "changePct",
  "cumulativeMainNetInflow",
];

export function exportMoneyFlowCsv(data: MoneyFlowSummaryResponse): void {
  const rows = data.items.flatMap((item) =>
    item.daily.map((daily) => [
      data.source,
      item.code,
      item.name,
      daily.tradeDate,
      daily.mainNetInflow,
      daily.superLargeInflow,
      daily.largeInflow,
      daily.mediumInflow,
      daily.smallInflow,
      daily.closePrice,
      daily.changePct,
      daily.cumulativeMainNetInflow,
    ]),
  );
  const csv = [COLUMNS, ...rows].map((row) => row.map(escapeCsvValue).join(",")).join("\n");
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `stock-flow-lens_${data.source}_${data.range.startDate}_${data.range.endDate}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function escapeCsvValue(value: string | number | null): string {
  if (value === null) {
    return "";
  }
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}
