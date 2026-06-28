"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RotateCcw, Upload } from "lucide-react";

/**
 * Dashboard-segment error boundary. Covers the candidate dashboard and the
 * chart-heavy AI insights page nested beneath it, so a rendering failure (e.g.
 * a chart library hiccup) shows a recoverable screen with the site chrome
 * intact instead of a blank page.
 */
export default function DashboardError({
  error, reset,
}: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error("Dashboard error:", error); }, [error]);

  return (
    <div className="page flex items-center justify-center">
      <div className="card-glass w-full max-w-md p-8 text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-500 ring-1 ring-red-100">
          <AlertTriangle size={26} />
        </div>
        <h1 className="text-xl font-bold tracking-[-0.01em] text-slate-900">We couldn’t render your dashboard</h1>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-slate-500">
          An unexpected error occurred while building this view. Retry to reload it, or upload a CV to refresh your insights.
        </p>
        {error?.digest && (
          <p className="mt-3 inline-block rounded-md bg-slate-100 px-2 py-1 font-mono text-2xs text-slate-400">ref: {error.digest}</p>
        )}
        <div className="mt-7 flex flex-col justify-center gap-2.5 sm:flex-row">
          <button onClick={reset} className="btn-primary !py-2.5"><RotateCcw size={15} /> Try again</button>
          <Link href="/upload" className="btn-outline !py-2.5"><Upload size={15} /> Upload CV</Link>
        </div>
      </div>
    </div>
  );
}
