"use client";

import { X, Search, ChevronLeft, ChevronRight, AlertTriangle, RotateCcw } from "lucide-react";
import type { ComponentType, ReactNode } from "react";

/* ── Accent system ──────────────────────────────────────────────────────────
   Each admin page carries a distinct accent so sections feel different while
   staying part of one family. */
export type Accent = "brand" | "sky" | "violet" | "amber" | "teal" | "rose";

export const ACCENT: Record<Accent, { tile: string; ring: string; soft: string; text: string; grad: string }> = {
  brand:  { tile: "bg-brand-600 text-white",  ring: "ring-brand-500/15",  soft: "bg-brand-50 text-brand-700",   text: "text-brand-600",  grad: "from-brand-500 to-accent-500" },
  sky:    { tile: "bg-sky-600 text-white",    ring: "ring-sky-500/15",    soft: "bg-sky-50 text-sky-700",       text: "text-sky-600",    grad: "from-sky-500 to-blue-500" },
  violet: { tile: "bg-violet-600 text-white", ring: "ring-violet-500/15", soft: "bg-violet-50 text-violet-700", text: "text-violet-600", grad: "from-violet-500 to-fuchsia-500" },
  amber:  { tile: "bg-amber-500 text-white",  ring: "ring-amber-500/15",  soft: "bg-amber-50 text-amber-700",   text: "text-amber-600",  grad: "from-amber-500 to-orange-500" },
  teal:   { tile: "bg-teal-600 text-white",   ring: "ring-teal-500/15",   soft: "bg-teal-50 text-teal-700",     text: "text-teal-600",   grad: "from-teal-500 to-emerald-500" },
  rose:   { tile: "bg-rose-500 text-white",   ring: "ring-rose-500/15",   soft: "bg-rose-50 text-rose-700",     text: "text-rose-600",   grad: "from-rose-500 to-pink-500" },
};

type IconType = ComponentType<{ size?: number | string }>;

export function AdminHeader({
  title, subtitle, icon: Icon, accent = "brand", action,
}: {
  title: string; subtitle?: string;
  icon?: IconType; accent?: Accent; action?: ReactNode;
}) {
  const a = ACCENT[accent];
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3.5">
        {Icon && (
          <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl shadow-sm ${a.tile}`}>
            <Icon size={20} />
          </span>
        )}
        <div>
          <h1 className="text-xl font-bold tracking-[-0.02em] text-slate-900 sm:text-2xl">{title}</h1>
          {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

export function Toolbar({ children }: { children: ReactNode }) {
  return <div className="mb-4 flex flex-wrap items-center gap-2">{children}</div>;
}

export function SearchBox({
  value, onChange, placeholder = "Search…",
}: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="relative w-full max-w-xs">
      <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-slate-200 bg-white/80 py-2 pl-9 pr-3 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 transition hover:border-slate-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/15"
      />
    </div>
  );
}

export function StatCard({
  label, value, icon: Icon, accent = "brand", sub, onClick,
}: {
  label: string; value: ReactNode; icon: IconType;
  accent?: Accent; sub?: string; onClick?: () => void;
}) {
  const a = ACCENT[accent];
  const cls = `group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 text-left shadow-card transition-all duration-200 ${onClick ? "hover:-translate-y-0.5 hover:shadow-lift" : ""}`;
  const inner = (
    <>
      <div className={`pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-gradient-to-br ${a.grad} opacity-[0.10] blur-xl`} />
      <div className="mb-3 flex items-center justify-between">
        <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${a.soft}`}><Icon size={18} /></span>
      </div>
      <p className="text-3xl font-extrabold tracking-tight text-slate-900 tabular-nums">{value}</p>
      <p className="mt-1 text-sm font-semibold text-slate-700">{label}</p>
      {sub && <p className="text-2xs text-slate-500">{sub}</p>}
    </>
  );
  return onClick
    ? <button onClick={onClick} className={cls}>{inner}</button>
    : <div className={cls}>{inner}</div>;
}

export function Pager({
  page, count, pageSize = 20, onPage, onPageSize,
}: { page: number; count: number; pageSize?: number; onPage: (p: number) => void; onPageSize?: (n: number) => void }) {
  const pages = Math.max(1, Math.ceil(count / pageSize));
  if (count === 0) return null;
  return (
    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
      <div className="flex items-center gap-3">
        <span>{count.toLocaleString()} total</span>
        {onPageSize && (
          <label className="flex items-center gap-1.5 text-xs text-slate-400">
            Rows
            <select
              value={pageSize}
              onChange={(e) => onPageSize(Number(e.target.value))}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              {[10, 20, 50, 100].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
        )}
      </div>
      <div className="flex items-center gap-2">
        <button disabled={page <= 1} onClick={() => onPage(page - 1)}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 shadow-sm transition hover:bg-slate-50 disabled:opacity-40">
          <ChevronLeft size={15} /> Prev
        </button>
        <span className="tabular-nums">Page {page} / {pages}</span>
        <button disabled={page >= pages} onClick={() => onPage(page + 1)}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 shadow-sm transition hover:bg-slate-50 disabled:opacity-40">
          Next <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}

export function Modal({
  open, title, subtitle, onClose, children,
}: { open: boolean; title: string; subtitle?: string; onClose: () => void; children: ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-pop animate-slide-up" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">{title}</h2>
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"><X size={18} /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

export function Badge({
  tone = "slate", children, dot,
}: { tone?: "slate" | "green" | "amber" | "red" | "blue" | "violet" | "teal" | "rose"; children: ReactNode; dot?: boolean }) {
  const map: Record<string, string> = {
    slate:  "bg-slate-100 text-slate-600 ring-slate-500/10",
    green:  "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
    amber:  "bg-amber-50 text-amber-700 ring-amber-600/15",
    red:    "bg-red-50 text-red-700 ring-red-600/15",
    blue:   "bg-sky-50 text-sky-700 ring-sky-600/15",
    violet: "bg-violet-50 text-violet-700 ring-violet-600/15",
    teal:   "bg-teal-50 text-teal-700 ring-teal-600/15",
    rose:   "bg-rose-50 text-rose-700 ring-rose-600/15",
  };
  const dotc: Record<string, string> = {
    slate: "bg-slate-400", green: "bg-emerald-500", amber: "bg-amber-500", red: "bg-red-500",
    blue: "bg-sky-500", violet: "bg-violet-500", teal: "bg-teal-500", rose: "bg-rose-500",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-semibold capitalize ring-1 ring-inset ${map[tone]}`}>
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dotc[tone]}`} />}
      {children}
    </span>
  );
}

export function Avatar({ name, email, accent = "brand" }: { name?: string; email?: string; accent?: Accent }) {
  const a = ACCENT[accent];
  const label = (name || email || "?").trim();
  const initials = label.includes(" ")
    ? label.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase()
    : label.slice(0, 2).toUpperCase();
  return (
    <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-2xs font-bold text-white ${a.grad}`}>
      {initials}
    </span>
  );
}

export function IconButton({
  onClick, title, tone = "slate", children,
}: { onClick: () => void; title: string; tone?: "slate" | "red"; children: ReactNode }) {
  const cls = tone === "red"
    ? "text-slate-400 hover:bg-red-50 hover:text-red-600"
    : "text-slate-400 hover:bg-slate-100 hover:text-slate-700";
  return (
    <button onClick={onClick} title={title} className={`rounded-lg p-1.5 transition ${cls}`}>{children}</button>
  );
}

export function TableShell({ head, children }: { head: ReactNode; children: ReactNode }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50/80 text-2xs font-semibold uppercase tracking-wide text-slate-500">
            {head}
          </thead>
          <tbody className="divide-y divide-slate-100">{children}</tbody>
        </table>
      </div>
    </div>
  );
}

export function TableSkeleton({ cols, rows = 6 }: { cols: number; rows?: number }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-card">
      <div className="divide-y divide-slate-100">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex items-center gap-4 px-4 py-3.5">
            {Array.from({ length: cols }).map((_, c) => (
              <div key={c} className="skeleton h-4" style={{ width: c === 0 ? "28%" : `${Math.max(8, 60 / cols)}%` }} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function TableError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-200/80 bg-white p-12 text-center shadow-card">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 text-red-500 ring-1 ring-red-100">
        <AlertTriangle size={22} />
      </span>
      <div>
        <p className="text-sm font-semibold text-slate-800">Couldn’t load this list</p>
        <p className="mx-auto mt-0.5 max-w-sm text-xs text-slate-500">{message}</p>
      </div>
      <button onClick={onRetry} className="btn-outline !py-1.5 !text-xs"><RotateCcw size={13} /> Retry</button>
    </div>
  );
}

export function EmptyRow({ colSpan, label = "Nothing here yet." }: { colSpan: number; label?: string }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-4 py-14 text-center">
        <p className="text-sm font-medium text-slate-500">{label}</p>
      </td>
    </tr>
  );
}
