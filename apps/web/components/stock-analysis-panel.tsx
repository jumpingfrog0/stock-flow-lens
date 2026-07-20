import { formatAmount, formatPercent } from "@/lib/format";
import type {
  Confidence,
  PrimaryDriver,
  StockMoveAnalysisResponse,
} from "@/types/stock-analysis";


type Props = {
  code: string;
  data: StockMoveAnalysisResponse | null;
  isLoading: boolean;
  error: string | null;
  onAnalyze: () => void;
};

const DRIVER_LABELS: Record<PrimaryDriver, string> = {
  market_rotation: "市场风格切换",
  industry_move: "行业板块共振",
  stock_specific: "个股独立驱动",
  mixed: "混合驱动",
  insufficient: "证据不足",
};

const CONFIDENCE_LABELS: Record<Confidence, string> = {
  high: "高置信度",
  medium: "中等置信度",
  low: "低置信度",
};

export function StockAnalysisPanel({ code, data, isLoading, error, onAnalyze }: Props) {
  return (
    <section className="rounded border border-border bg-white p-5 shadow-surface">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-ink">股票涨跌自动归因</h2>
          <p className="mt-1 text-sm text-muted">
            按市场风格、行业共振、个股独立因素和反事实检验依次分析。
          </p>
        </div>
        <button
          type="button"
          onClick={onAnalyze}
          disabled={isLoading}
          className="h-9 rounded bg-accent px-4 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "分析中…" : `分析 ${code}`}
        </button>
      </div>

      {error ? <div className="mt-4 rounded bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      {!data && !error ? (
        <div className="mt-4 rounded border border-dashed border-border px-4 py-6 text-center text-sm text-muted">
          点击分析后，将读取最新行情、市场风格、同行表现和公司公告。
        </div>
      ) : null}

      {data ? (
        <div className="mt-5 space-y-5">
          <div className="rounded bg-slate-50 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-lg font-semibold text-ink">
                {data.stock.name} {data.stock.code}
              </span>
              <span className="rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
                {DRIVER_LABELS[data.primaryDriver]}
              </span>
              <span className="rounded bg-slate-200 px-2 py-1 text-xs text-slate-700">
                {CONFIDENCE_LABELS[data.confidence]}
              </span>
              <span className="text-xs text-muted">截至 {data.asOf}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-700">{data.summary}</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="个股涨跌" value={formatPercent(data.stock.changePct)} />
            <Metric
              label={`相对${data.market.benchmarkName}`}
              value={formatPercent(data.stock.marketRelativePct)}
            />
            <Metric label="相对行业" value={formatPercent(data.stock.industryRelativePct)} />
            <Metric label="价值减成长" value={formatPercent(data.style.valueMinusGrowthPct)} />
            <Metric label="主力资金" value={formatAmount(data.stock.mainNetInflow)} />
            <Metric label="成交额" value={formatAmount(data.stock.amount)} />
            <Metric label="换手率" value={formatPercent(data.stock.turnoverRate)} />
            <Metric
              label="市场上涨占比"
              value={
                data.market.breadth
                  ? formatPercent(data.market.breadth.advancingRatio * 100)
                  : "-"
              }
            />
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {data.drivers.map((driver) => (
              <article key={driver.code} className="rounded border border-border p-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold text-ink">{driver.label}</h3>
                  <span className="text-sm font-semibold text-accent">{driver.score}/100</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded bg-slate-100">
                  <div className="h-full rounded bg-accent" style={{ width: `${driver.score}%` }} />
                </div>
                <ul className="mt-3 space-y-1.5 text-sm text-slate-700">
                  {driver.evidence.length ? (
                    driver.evidence.map((item) => <li key={item}>· {item}</li>)
                  ) : (
                    <li className="text-muted">暂无支持证据</li>
                  )}
                </ul>
                {driver.limitations.length ? (
                  <div className="mt-3 border-t border-border pt-3 text-xs leading-5 text-muted">
                    {driver.limitations.join("；")}
                  </div>
                ) : null}
              </article>
            ))}
          </div>

          <div>
            <h3 className="text-sm font-semibold text-ink">反事实检验</h3>
            <div className="mt-2 grid gap-2 md:grid-cols-3">
              {data.counterfactuals.map((item) => (
                <div key={item.code} className="rounded border border-border px-3 py-3 text-sm text-slate-700">
                  <span className={counterfactualClass(item.result)}>
                    {counterfactualLabel(item.result)}
                  </span>
                  <p className="mt-2 leading-5">{item.conclusion}</p>
                </div>
              ))}
            </div>
          </div>

          {data.warnings.length ? (
            <div className="rounded bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
              {data.warnings.join("；")}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-border px-3 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}

function counterfactualLabel(result: "supports" | "weakens" | "unknown"): string {
  if (result === "supports") return "支持";
  if (result === "weakens") return "削弱";
  return "未知";
}

function counterfactualClass(result: "supports" | "weakens" | "unknown"): string {
  if (result === "supports") return "font-medium text-positive";
  if (result === "weakens") return "font-medium text-negative";
  return "font-medium text-muted";
}
