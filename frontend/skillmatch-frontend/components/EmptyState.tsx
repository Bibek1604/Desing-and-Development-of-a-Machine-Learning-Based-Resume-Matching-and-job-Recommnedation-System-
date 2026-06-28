"use client";

import { Inbox } from "lucide-react";
import Link from "next/link";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message?: string;
  actionHref?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

/** Consistent empty-data panel (no results, nothing uploaded yet, etc.). */
export default function EmptyState({
  icon,
  title,
  message,
  actionHref,
  actionLabel,
  onAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`card flex flex-col items-center justify-center gap-3 px-6 py-12 text-center ${className}`}>
      <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-500 ring-1 ring-inset ring-brand-100">
        {icon ?? <Inbox className="h-6 w-6" />}
      </span>
      <div className="max-w-sm space-y-1.5">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        {message && <p className="text-sm leading-relaxed text-slate-500">{message}</p>}
      </div>
      {actionHref && actionLabel && (
        <Link href={actionHref} className="btn-primary">{actionLabel}</Link>
      )}
      {onAction && actionLabel && !actionHref && (
        <button type="button" onClick={onAction} className="btn-primary">{actionLabel}</button>
      )}
    </div>
  );
}
