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
