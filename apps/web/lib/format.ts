import type { Direction } from "@/types/money-flow";

export function formatAmount(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  const abs = Math.abs(value);
  if (abs >= 100000000) {
    return `${(value / 100000000).toFixed(2)} 亿`;
  }
  if (abs >= 10000) {
    return `${(value / 10000).toFixed(2)} 万`;
  }
  return value.toFixed(2);
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return `${value.toFixed(2)}%`;
}

export function directionLabel(direction: Direction, amount: number): string {
  if (direction === "inflow") {
    return `净流入 ${formatAmount(amount)}`;
  }
  if (direction === "outflow") {
    return `净流出 ${formatAmount(amount)}`;
  }
  return "持平";
}

export function directionClass(direction: Direction): string {
  if (direction === "inflow") {
    return "text-positive";
  }
  if (direction === "outflow") {
    return "text-negative";
  }
  return "text-muted";
}

export function defaultDateRange(): { startDate: string; endDate: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 30);
  return {
    startDate: toDateInputValue(start),
    endDate: toDateInputValue(end),
  };
}

function toDateInputValue(date: Date): string {
  return date.toISOString().slice(0, 10);
}
