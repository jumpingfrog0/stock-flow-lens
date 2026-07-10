export type Direction = "inflow" | "outflow" | "flat";

export type DailyMoneyFlow = {
  tradeDate: string;
  mainNetInflow: number;
  superLargeInflow: number | null;
  largeInflow: number | null;
  mediumInflow: number | null;
  smallInflow: number | null;
  closePrice: number | null;
  changePct: number | null;
  cumulativeMainNetInflow: number;
};

export type MoneyFlowItem = {
  code: string;
  name: string;
  mainNetInflow: number;
  direction: Direction;
  directionAmount: number;
  tradeDays: number;
  daily: DailyMoneyFlow[];
};

export type MoneyFlowError = {
  code: string | null;
  errorCode: string;
  message: string;
};

export type MoneyFlowSummaryResponse = {
  range: {
    startDate: string;
    endDate: string;
  };
  items: MoneyFlowItem[];
  totalMainNetInflow: number;
  totalDirection: Direction;
  totalDirectionAmount: number;
  errors: MoneyFlowError[];
};

export type MoneyFlowSummaryRequest = {
  symbols: string[];
  startDate: string;
  endDate: string;
  source: "eastmoney";
};

export type MoneyFlowRefreshRecentRequest = {
  symbols: string[];
  source: "eastmoney";
};

export type MoneyFlowRefreshRecentItem = {
  code: string;
  name: string;
  refreshedRows: number;
};

export type MoneyFlowRefreshRecentResponse = {
  range: {
    startDate: string;
    endDate: string;
  };
  items: MoneyFlowRefreshRecentItem[];
  errors: MoneyFlowError[];
};

export type StockSearchItem = {
  code: string;
  name: string;
  market: string;
  secid: string;
  industry: string | null;
  updatedAt: string;
};

export type StockRefreshRequest = {
  query?: string;
  limit?: number;
};

export type StockRefreshResponse = {
  refreshed: number;
};

export type QueryHistoryItem = {
  id: number;
  symbols: string[];
  startDate: string;
  endDate: string;
  source: string;
  createdAt: string;
};

export type QueryHistoryCreateRequest = {
  symbols: string[];
  startDate: string;
  endDate: string;
  source: "eastmoney";
};

export type WatchlistItem = {
  id: number;
  stock: StockSearchItem;
  createdAt: string;
};

export type Watchlist = {
  id: number;
  name: string;
  createdAt: string;
  updatedAt: string;
  items: WatchlistItem[];
};

export type BoardType = "industry" | "concept";

export type BoardSearchItem = {
  code: string;
  name: string;
  type: BoardType;
  market: string;
  secid: string;
  source: "eastmoney";
};

export type BoardFlowSummaryRequest = {
  boards: string[];
  startDate: string;
  endDate: string;
  type: BoardType;
  source: "eastmoney";
};

export type BoardFlowSummaryResponse = MoneyFlowSummaryResponse;
