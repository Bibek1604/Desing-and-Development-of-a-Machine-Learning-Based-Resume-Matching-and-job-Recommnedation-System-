"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

/**
 * Route-segment error boundary. Next.js renders this whenever a client/server
 * component below it throws during render, so an unexpected UI crash shows a
 * recoverable screen instead of a blank page.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface to monitoring in production; console for local dev.
    console.error("Unhandled UI error:", error);
  }, [error]);

  return (
    <div className="page flex items-center justify-center">
      <div className="card mx-auto max-w-md px-6 py-12 text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-red-50 text-red-600 ring-1 ring-inset ring-red-100">
          <AlertTriangle className="h-6 w-6" />
        </span>
        <h1 className="mt-4 text-xl font-bold text-slate-900">Something went wrong</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          We hit an unexpected error while loading this page. You can try again,
          or head back to the dashboard.
        </p>
        {error.digest && (
          <p className="mt-3 font-mono text-xs text-slate-500">Reference: {error.digest}</p>
        )}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2.5">
          <button type="button" onClick={reset} className="btn-primary">
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
          <Link href="/" className="btn-outline">
            <Home className="h-4 w-4" />
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}
