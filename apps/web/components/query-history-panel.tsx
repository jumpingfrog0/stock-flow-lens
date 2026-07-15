import { RotateCcw } from "lucide-react";

import type { QueryHistoryItem } from "@/types/money-flow";

type QueryHistoryPanelProps = {
  items: QueryHistoryItem[];
  isLoading: boolean;
  onReuse: (item: QueryHistoryItem) => void;
};

export function QueryHistoryPanel({ items, isLoading, onReuse }: QueryHistoryPanelProps) {
  return (
    <section className="rounded border border-border bg-panel shadow-surface">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-base font-semibold text-ink">最近历史</h2>
      </div>
      <div className="max-h-80 overflow-auto p-3">
        {isLoading ? <div className="px-1 py-2 text-sm text-muted">加载中...</div> : null}
        {!isLoading && items.length === 0 ? (
          <div className="px-1 py-2 text-sm text-muted">暂无查询历史</div>
        ) : null}
        <div className="flex flex-col gap-2">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onReuse(item)}
              className="rounded border border-border bg-white p-3 text-left transition hover:border-accent hover:bg-blue-50"
              title="复用并立即查询"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="truncate text-sm font-medium text-ink">{item.symbols.join(", ")}</span>
                <RotateCcw className="h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
              </div>
              <div className="mt-1 text-xs text-muted">
                {item.startDate} 至 {item.endDate} · {sourceLabel(item.source)}
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

function sourceLabel(source: QueryHistoryItem["source"]): string {
  return source === "akshare" ? "AKShare" : "东方财富直连";
}
