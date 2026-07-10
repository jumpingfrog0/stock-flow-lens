import { utils, writeFile } from "xlsx";

import type { MoneyFlowSummaryResponse } from "@/types/money-flow";

const COLUMNS = [
  "code",
  "name",
  "tradeDate",
  "mainNetInflow",
  "superLargeInflow",
  "largeInflow",
  "mediumInflow",
  "smallInflow",
  "closePrice",
  "changePct",
  "cumulativeMainNetInflow",
];

export function exportMoneyFlowExcel(data: MoneyFlowSummaryResponse): void {
  const rows = data.items.flatMap((item) =>
    item.daily.map((daily) => ({
      code: item.code,
      name: item.name,
      tradeDate: daily.tradeDate,
      mainNetInflow: daily.mainNetInflow,
      superLargeInflow: daily.superLargeInflow,
      largeInflow: daily.largeInflow,
      mediumInflow: daily.mediumInflow,
      smallInflow: daily.smallInflow,
      closePrice: daily.closePrice,
      changePct: daily.changePct,
      cumulativeMainNetInflow: daily.cumulativeMainNetInflow,
    })),
  );
  const worksheet = utils.json_to_sheet(rows, { header: COLUMNS });
  const workbook = utils.book_new();
  utils.book_append_sheet(workbook, worksheet, "money-flow");
  writeFile(workbook, `stock-flow-lens_${data.range.startDate}_${data.range.endDate}.xlsx`);
}
