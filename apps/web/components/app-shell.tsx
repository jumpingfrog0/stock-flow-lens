import Link from "next/link";

type Tool = "money-flow" | "attribution";

type Props = {
  active: Tool;
  children: React.ReactNode;
};

const TOOLS: Array<{ key: Tool; href: string; label: string }> = [
  { key: "money-flow", href: "/money-flow", label: "资金流透镜" },
  { key: "attribution", href: "/attribution", label: "股票涨跌归因" },
];

export function AppShell({ active, children }: Props) {
  return (
    <main className="min-h-screen bg-slate-100">
      <div className="border-b border-border bg-white">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-6">
          <Link href="/money-flow" className="text-lg font-semibold text-ink">
            A股研究工具箱
          </Link>
          <nav aria-label="研究工具" className="flex flex-wrap gap-2">
            {TOOLS.map((tool) => (
              <Link
                key={tool.key}
                href={tool.href}
                aria-current={active === tool.key ? "page" : undefined}
                className={`rounded px-3 py-2 text-sm font-medium transition ${
                  active === tool.key
                    ? "bg-accent text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-ink"
                }`}
              >
                {tool.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
      <div className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</div>
    </main>
  );
}
