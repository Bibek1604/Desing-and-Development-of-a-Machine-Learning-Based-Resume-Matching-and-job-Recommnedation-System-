"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RotateCcw, LayoutDashboard } from "lucide-react";

/**
 * Admin-segment error boundary. Renders inside the admin shell (sidebar +
 * topbar stay visible) so an error in any admin page degrades in-context
 * rather than dropping the user onto the generic public error screen.
 */
export default function AdminError({
  error, reset,
}: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error("Admin error:", error); }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-md rounded-2xl border border-slate-200/80 bg-white p-8 text-center shadow-card">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-500 ring-1 ring-red-100">
          <AlertTriangle size={26} />
        </div>
        <h1 className="text-lg font-bold text-slate-900">This admin view hit an error</h1>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-slate-500">
          Something went wrong loading this section. You can retry, or return to the dashboard.
        </p>
        {error?.digest && (
          <p className="mt-3 inline-block rounded-md bg-slate-100 px-2 py-1 font-mono text-2xs text-slate-400">ref: {error.digest}</p>
        )}
        <div className="mt-7 flex flex-col justify-center gap-2.5 sm:flex-row">
          <button onClick={reset} className="btn-primary !py-2.5"><RotateCcw size={15} /> Try again</button>
          <Link href="/admin" className="btn-outline !py-2.5"><LayoutDashboard size={15} /> Admin home</Link>
        </div>
      </div>
    </div>
  );
}
