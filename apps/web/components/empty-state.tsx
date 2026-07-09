import { Search } from "lucide-react";

type EmptyStateProps = {
  title?: string;
  message?: string;
};

export function EmptyState({
  title = "尚未查询",
  message = "输入股票代码和日期区间后开始查询。",
}: EmptyStateProps) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded border border-dashed border-border bg-white px-4 py-8 text-center">
      <Search className="h-8 w-8 text-muted" aria-hidden="true" />
      <div className="mt-3 text-base font-medium text-ink">{title}</div>
      <div className="mt-1 text-sm text-muted">{message}</div>
    </div>
  );
}
