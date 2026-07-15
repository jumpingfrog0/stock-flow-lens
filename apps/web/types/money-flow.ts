export type Direction = "inflow" | "outflow" | "flat";
export type DataSource = "akshare" | "eastmoney";

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
  source: DataSource;
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
  source: DataSource;
};

export type MoneyFlowRefreshRecentRequest = {
  symbols: string[];
  source: DataSource;
};

export type MoneyFlowRefreshRecentItem = {
  code: string;
  name: string;
  refreshedRows: number;
};

export type MoneyFlowRefreshRecentResponse = {
  source: DataSource;
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
  source?: DataSource;
};

export type StockRefreshResponse = {
  refreshed: number;
};

export type QueryHistoryItem = {
  id: number;
  symbols: string[];
  startDate: string;
  endDate: string;
  source: DataSource;
  createdAt: string;
};

export type QueryHistoryCreateRequest = {
  symbols: string[];
  startDate: string;
  endDate: string;
  source: DataSource;
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
  source: DataSource;
};

export type BoardFlowSummaryRequest = {
  boards: string[];
  startDate: string;
  endDate: string;
  type: BoardType;
  source: DataSource;
};

export type BoardFlowSummaryResponse = MoneyFlowSummaryResponse;
