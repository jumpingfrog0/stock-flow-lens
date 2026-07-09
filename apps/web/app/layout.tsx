import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "资金流透镜",
  description: "A 股资金流统计、本地缓存与可视化工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
