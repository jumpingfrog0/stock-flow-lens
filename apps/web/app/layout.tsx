import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "A股研究工具箱",
    template: "%s | A股研究工具箱",
  },
  description: "面向 A 股的资金流查询与股票涨跌归因工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
