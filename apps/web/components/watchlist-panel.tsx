"use client";

import { Check, Pencil, Plus, Search, Trash2, X } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import type { Watchlist } from "@/types/money-flow";

type WatchlistPanelProps = {
  watchlists: Watchlist[];
  isLoading: boolean;
  onCreate: (name: string) => Promise<void>;
  onRename: (id: number, name: string) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onAddItem: (id: number, symbol: string) => Promise<void>;
  onRemoveItem: (id: number, symbol: string) => Promise<void>;
  onQuery: (symbols: string[]) => void;
};

export function WatchlistPanel({
  watchlists,
  isLoading,
  onCreate,
  onRename,
  onDelete,
  onAddItem,
  onRemoveItem,
  onQuery,
}: WatchlistPanelProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const [newSymbol, setNewSymbol] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");
  const [pending, setPending] = useState(false);

  const selected = useMemo(() => {
    if (watchlists.length === 0) {
      return null;
    }
    return watchlists.find((item) => item.id === selectedId) ?? watchlists[0];
  }, [selectedId, watchlists]);

  async function submitCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) {
      return;
    }
    setPending(true);
    try {
      await onCreate(name);
      setNewName("");
    } finally {
      setPending(false);
    }
  }

  async function submitAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const symbol = newSymbol.trim();
    if (!symbol || !selected) {
      return;
    }
    setPending(true);
    try {
      await onAddItem(selected.id, symbol);
      setNewSymbol("");
    } finally {
      setPending(false);
    }
  }

  async function submitRename(id: number) {
    const name = editingName.trim();
    if (!name) {
      return;
    }
    setPending(true);
    try {
      await onRename(id, name);
      setEditingId(null);
      setEditingName("");
    } finally {
      setPending(false);
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm("确认删除该自选分组？")) {
      return;
    }
    setPending(true);
    try {
      await onDelete(id);
      if (selectedId === id) {
        setSelectedId(null);
      }
    } finally {
      setPending(false);
    }
  }

  const selectedSymbols = selected?.items.map((item) => item.stock.code) ?? [];

  return (
    <section className="rounded border border-border bg-panel shadow-surface">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-base font-semibold text-ink">自选股</h2>
      </div>
      <div className="grid gap-3 p-3 lg:grid-cols-[220px_1fr]">
        <div className="flex flex-col gap-2">
          <form onSubmit={submitCreate} className="flex gap-2">
            <input
              value={newName}
              onChange={(event) => setNewName(event.target.value)}
              className="h-9 min-w-0 flex-1 rounded border border-border bg-white px-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-blue-100"
              placeholder="新分组"
            />
            <button
              type="submit"
              disabled={pending || !newName.trim()}
              className="inline-flex h-9 w-9 items-center justify-center rounded border border-border bg-white text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
              title="创建分组"
            >
              <Plus className="h-4 w-4" />
            </button>
          </form>

          <div className="flex max-h-72 flex-col gap-1 overflow-auto">
            {isLoading ? <div className="px-2 py-2 text-sm text-muted">加载中...</div> : null}
            {!isLoading && watchlists.length === 0 ? (
              <div className="px-2 py-2 text-sm text-muted">暂无自选分组</div>
            ) : null}
            {watchlists.map((list) => (
              <div key={list.id} className="flex items-center gap-1">
                {editingId === list.id ? (
                  <>
                    <input
                      value={editingName}
                      onChange={(event) => setEditingName(event.target.value)}
                      className="h-9 min-w-0 flex-1 rounded border border-border px-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-blue-100"
                    />
                    <button
                      type="button"
                      onClick={() => submitRename(list.id)}
                      className="inline-flex h-9 w-9 items-center justify-center rounded border border-border bg-white text-ink hover:bg-slate-50"
                      title="保存名称"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="inline-flex h-9 w-9 items-center justify-center rounded border border-border bg-white text-ink hover:bg-slate-50"
                      title="取消"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => setSelectedId(list.id)}
                      className={`min-w-0 flex-1 rounded border px-3 py-2 text-left text-sm transition ${
                        selected?.id === list.id
                          ? "border-accent bg-blue-50 text-ink"
                          : "border-border bg-white text-ink hover:bg-slate-50"
                      }`}
                    >
                      <span className="block truncate font-medium">{list.name}</span>
                      <span className="text-xs text-muted">{list.items.length} 只</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingId(list.id);
                        setEditingName(list.name);
                      }}
                      className="inline-flex h-9 w-9 items-center justify-center rounded border border-border bg-white text-ink hover:bg-slate-50"
                      title="重命名"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(list.id)}
                      className="inline-flex h-9 w-9 items-center justify-center rounded border border-border bg-white text-negative hover:bg-red-50"
                      title="删除分组"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="min-w-0">
          {selected ? (
            <>
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="text-sm font-medium text-ink">{selected.name}</div>
                  <div className="text-xs text-muted">按分组批量查询或维护成分股</div>
                </div>
                <button
                  type="button"
                  disabled={selectedSymbols.length === 0}
                  onClick={() => onQuery(selectedSymbols)}
                  className="inline-flex h-9 items-center justify-center gap-2 rounded bg-accent px-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  title="查询该分组"
                >
                  <Search className="h-4 w-4" />
                  查询分组
                </button>
              </div>

              <form onSubmit={submitAdd} className="mt-3 flex gap-2">
                <input
                  value={newSymbol}
                  onChange={(event) => setNewSymbol(event.target.value)}
                  className="h-9 min-w-0 flex-1 rounded border border-border bg-white px-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-blue-100"
                  placeholder="输入代码或名称添加"
                />
                <button
                  type="submit"
                  disabled={pending || !newSymbol.trim()}
                  className="inline-flex h-9 items-center justify-center gap-2 rounded border border-border bg-white px-3 text-sm font-medium text-ink hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
                  title="添加自选股"
                >
                  <Plus className="h-4 w-4" />
                  添加
                </button>
              </form>

              <div className="mt-3 flex max-h-56 flex-wrap gap-2 overflow-auto">
                {selected.items.length === 0 ? (
                  <div className="text-sm text-muted">该分组还没有股票</div>
                ) : null}
                {selected.items.map((item) => (
                  <span
                    key={item.id}
                    className="inline-flex items-center gap-2 rounded border border-border bg-white px-2 py-1 text-sm text-ink"
                  >
                    <span>{item.stock.name}</span>
                    <span className="text-xs text-muted">{item.stock.code}</span>
                    <button
                      type="button"
                      onClick={() => onRemoveItem(selected.id, item.stock.code)}
                      className="text-muted transition hover:text-negative"
                      title="移除"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="rounded border border-dashed border-border bg-slate-50 px-3 py-8 text-center text-sm text-muted">
              创建或选择一个自选分组
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
