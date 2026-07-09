import type { MoneyFlowItem } from "@/types/money-flow";
import { formatAmount, formatPercent } from "@/lib/format";

type DailyDetailTableProps = {
  item: MoneyFlowItem;
};

export function DailyDetailTable({ item }: DailyDetailTableProps) {
  return (
    <div className="overflow-hidden rounded border border-border bg-panel shadow-surface">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-base font-semibold text-ink">每日明细</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-muted">
            <tr>
              <th className="px-4 py-3">日期</th>
              <th className="px-4 py-3 text-right">主力</th>
              <th className="px-4 py-3 text-right">超大单</th>
              <th className="px-4 py-3 text-right">大单</th>
              <th className="px-4 py-3 text-right">中单</th>
              <th className="px-4 py-3 text-right">小单</th>
              <th className="px-4 py-3 text-right">收盘价</th>
              <th className="px-4 py-3 text-right">涨跌幅</th>
              <th className="px-4 py-3 text-right">累计</th>
            </tr>
          </thead>
          <tbody>
            {item.daily.map((row) => (
              <tr key={row.tradeDate} className="border-t border-border bg-white">
                <td className="px-4 py-3 font-medium text-ink">{row.tradeDate}</td>
                <td className="px-4 py-3 text-right">{formatAmount(row.mainNetInflow)}</td>
                <td className="px-4 py-3 text-right">{formatAmount(row.superLargeInflow)}</td>
                <td className="px-4 py-3 text-right">{formatAmount(row.largeInflow)}</td>
                <td className="px-4 py-3 text-right">{formatAmount(row.mediumInflow)}</td>
                <td className="px-4 py-3 text-right">{formatAmount(row.smallInflow)}</td>
                <td className="px-4 py-3 text-right">{row.closePrice ?? "-"}</td>
                <td className="px-4 py-3 text-right">{formatPercent(row.changePct)}</td>
                <td className="px-4 py-3 text-right">{formatAmount(row.cumulativeMainNetInflow)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
