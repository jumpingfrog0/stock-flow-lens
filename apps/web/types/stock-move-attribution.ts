export type PrimaryDriver =
  | "market_rotation"
  | "industry_move"
  | "stock_specific"
  | "mixed"
  | "insufficient";

export type Confidence = "high" | "medium" | "low";
export type RotationDirection = "high_to_low" | "low_to_high" | "balanced";

export type DriverEvidence = {
  code: "market_rotation" | "industry_move" | "stock_specific";
  label: string;
  score: number;
  evidence: string[];
  limitations: string[];
};

export type StockMoveAttributionResponse = {
  methodologyVersion: string;
  source: string;
  asOf: string;
  primaryDriver: PrimaryDriver;
  confidence: Confidence;
  summary: string;
  stock: {
    code: string;
    name: string;
    tradeDate: string;
    industry: string | null;
    styleBucket: "growth" | "defensive_value" | "unclassified";
    closePrice: number;
    changePct: number;
    openPrice: number | null;
    highPrice: number | null;
    lowPrice: number | null;
    previousClose: number | null;
    amount: number | null;
    turnoverRate: number | null;
    volumeRatio: number | null;
    mainNetInflow: number | null;
    marketRelativePct: number | null;
    industryRelativePct: number | null;
  };
  market: {
    benchmarkKey: string;
    benchmarkName: string;
    benchmarkChangePct: number;
    benchmarks: Array<{
      key: string;
      name: string;
      group: string;
      changePct: number;
    }>;
    breadth: {
      total: number;
      advancing: number;
      declining: number;
      flat: number;
      advancingRatio: number;
    } | null;
  };
  style: {
    rotation: RotationDirection;
    growthProxyChangePct: number | null;
    valueProxyChangePct: number | null;
    valueMinusGrowthPct: number | null;
    note: string;
  };
  industry: {
    code: string;
    name: string;
    changePct: number | null;
    mainNetInflow: number | null;
    peerCount: number;
    advancing: number;
    declining: number;
    flat: number;
    advancingRatio: number | null;
    medianChangePct: number | null;
  } | null;
  announcements: Array<{
    title: string;
    noticeDate: string;
    artCode: string;
    sameDay: boolean;
  }>;
  drivers: DriverEvidence[];
  counterfactuals: Array<{
    code: "peers_move_together" | "style_rotation" | "same_day_announcement";
    result: "supports" | "weakens" | "unknown";
    conclusion: string;
  }>;
  warnings: string[];
};
