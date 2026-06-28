"use client";

import { AlertTriangle, RefreshCw, WifiOff, Lock, SearchX } from "lucide-react";
import Link from "next/link";

type Variant = "error" | "network" | "auth" | "empty";

const VARIANT_ICON: Record<Variant, React.ReactNode> = {
  error:   <AlertTriangle className="h-6 w-6" />,
  network: <WifiOff className="h-6 w-6" />,
  auth:    <Lock className="h-6 w-6" />,
  empty:   <SearchX className="h-6 w-6" />,
};

const VARIANT_TONE: Record<Variant, string> = {
  error:   "bg-red-50 text-red-600 ring-red-100",
  network: "bg-amber-50 text-amber-600 ring-amber-100",
  auth:    "bg-brand-50 text-brand-600 ring-brand-100",
  empty:   "bg-slate-100 text-slate-500 ring-slate-200",
};

export interface ErrorStateProps {
  variant?: Variant;
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  /** Optional secondary action, e.g. a link back home. */
  actionHref?: string;
  actionLabel?: string;
  className?: string;
}

/**
 * Friendly, reusable error / empty panel. Used across pages so failures look
 * intentional and consistent rather than a blank screen or raw message.
 */
export default function ErrorState({
  variant = "error",
  title,
  message,
  onRetry,
  retryLabel = "Try again",
  actionHref,
  actionLabel,
  className = "",
}: ErrorStateProps) {
  const fallbackTitle =
    variant === "network" ? "Connection problem" :
    variant === "auth"    ? "Sign in required" :
    variant === "empty"   ? "Nothing here yet" :
                            "Something went wrong";
  const fallbackMessage =
    variant === "network" ? "We couldn't reach the server. Check your connection and try again." :
    variant === "auth"    ? "Your session may have expired. Please sign in to continue." :
    variant === "empty"   ? "There's no data to show right now." :
                            "An unexpected error occurred. Please try again in a moment.";

  return (
    <div
      role={variant === "empty" ? undefined : "alert"}
      className={`card flex flex-col items-center justify-center gap-4 px-6 py-12 text-center ${className}`}
    >
      <span className={`flex h-14 w-14 items-center justify-center rounded-xl ring-1 ring-inset ${VARIANT_TONE[variant]}`}>
        {VARIANT_ICON[variant]}
      </span>
      <div className="max-w-sm space-y-1.5">
        <h3 className="text-base font-semibold text-slate-900">{title ?? fallbackTitle}</h3>
        <p className="text-sm leading-relaxed text-slate-500">{message ?? fallbackMessage}</p>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-2.5">
        {onRetry && (
          <button type="button" onClick={onRetry} className="btn-primary">
            <RefreshCw className="h-4 w-4" />
            {retryLabel}
          </button>
        )}
        {actionHref && actionLabel && (
          <Link href={actionHref} className="btn-outline">
            {actionLabel}
          </Link>
        )}
      </div>
    </div>
  );
}

/** Compact inline variant for smaller surfaces (cards, panels). */
export function InlineError({
  message,
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex items-center gap-3 rounded-lg border border-red-200/70 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      <AlertTriangle className="h-4 w-4 shrink-0" />
      <span className="flex-1">{message ?? "Couldn't load this section."}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1 font-semibold text-red-700 hover:text-red-900"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </button>
      )}
    </div>
  );
}
