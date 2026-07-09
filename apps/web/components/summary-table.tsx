import type { MoneyFlowItem } from "@/types/money-flow";
import { directionClass, directionLabel, formatAmount } from "@/lib/format";

type SummaryTableProps = {
  items: MoneyFlowItem[];
  selectedCode: string | null;
  onSelect: (code: string) => void;
};

export function SummaryTable({ items, selectedCode, onSelect }: SummaryTableProps) {
  return (
    <div className="overflow-hidden rounded border border-border bg-panel shadow-surface">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-base font-semibold text-ink">区间统计</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-muted">
            <tr>
              <th className="px-4 py-3">代码</th>
              <th className="px-4 py-3">名称</th>
              <th className="px-4 py-3 text-right">交易日</th>
              <th className="px-4 py-3 text-right">主力净流入</th>
              <th className="px-4 py-3 text-right">方向</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.code}
                onClick={() => onSelect(item.code)}
                className={`cursor-pointer border-t border-border transition hover:bg-blue-50 ${
                  selectedCode === item.code ? "bg-blue-50" : "bg-white"
                }`}
              >
                <td className="px-4 py-3 font-medium text-ink">{item.code}</td>
                <td className="px-4 py-3 text-ink">{item.name}</td>
                <td className="px-4 py-3 text-right text-muted">{item.tradeDays}</td>
                <td className={`px-4 py-3 text-right font-medium ${directionClass(item.direction)}`}>
                  {formatAmount(item.mainNetInflow)}
                </td>
                <td className={`px-4 py-3 text-right ${directionClass(item.direction)}`}>
                  {directionLabel(item.direction, item.directionAmount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
