"use client";

import { useEffect } from "react";

/**
 * Root-level error boundary. Catches failures in the root layout itself (where
 * the normal error.tsx cannot render). It must include its own <html>/<body>.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Fatal application error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f8fafc",
          fontFamily: "Inter, system-ui, sans-serif",
          color: "#0f172a",
        }}
      >
        <div
          style={{
            maxWidth: 420,
            padding: "2.5rem 1.5rem",
            textAlign: "center",
            background: "#fff",
            borderRadius: 16,
            border: "1px solid #e2e8f0",
            boxShadow: "0 10px 30px rgba(2,6,23,0.06)",
          }}
        >
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 8px" }}>
            Application error
          </h1>
          <p style={{ fontSize: 14, color: "#64748b", lineHeight: 1.6, margin: "0 0 24px" }}>
            A critical error occurred. Please reload the page — if the problem
            persists, try again later.
          </p>
          <button
            type="button"
            onClick={reset}
            style={{
              padding: "10px 20px",
              fontSize: 14,
              fontWeight: 600,
              color: "#fff",
              background: "#059669",
              border: "none",
              borderRadius: 12,
              cursor: "pointer",
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
