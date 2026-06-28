"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

/**
 * Reusable component-level error boundary. Wrap any non-critical widget (a
 * chart, a table, a panel) so a runtime error inside it shows a small inline
 * fallback instead of crashing the whole page. Optionally pass a custom
 * `fallback`. `label` names the widget in the default fallback.
 */
interface Props { children: ReactNode; fallback?: ReactNode; label?: string }
interface State { hasError: boolean }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    console.error("ErrorBoundary caught:", error);
  }

  reset = () => this.setState({ hasError: false });

  render() {
    if (!this.state.hasError) return this.props.children;
    if (this.props.fallback) return this.props.fallback;

    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-slate-200/80 bg-white p-8 text-center shadow-card">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-50 text-amber-500 ring-1 ring-amber-100">
          <AlertTriangle size={20} />
        </span>
        <div>
          <p className="text-sm font-semibold text-slate-800">
            {this.props.label ? `Couldn't load ${this.props.label}` : "Couldn't load this section"}
          </p>
          <p className="mt-0.5 text-xs text-slate-500">It ran into a problem. Try reloading it.</p>
        </div>
        <button onClick={this.reset} className="btn-outline !py-1.5 !text-xs">
          <RotateCcw size={13} /> Retry
        </button>
      </div>
    );
  }
}
