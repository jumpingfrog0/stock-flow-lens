import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "资金流透镜",
  description: "A 股个股与板块区间资金流查询、缓存、统计和可视化",
};

export default function MoneyFlowLayout({ children }: { children: React.ReactNode }) {
  return children;
}
