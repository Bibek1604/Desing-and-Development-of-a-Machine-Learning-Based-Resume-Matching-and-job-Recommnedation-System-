"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  ClipboardList, MapPin, Clock, Trash2, Send, ArrowRight,
} from "lucide-react";
import { useRequireAuth } from "@/context/AuthContext";
import { applications as applicationsApi, humanizeError, type Application } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import ErrorState from "@/components/ErrorState";
import Spinner from "@/components/Spinner";

const STATUS_STYLE: Record<string, string> = {
  applied:     "bg-brand-50 text-brand-700 ring-brand-600/15",
  reviewed:    "bg-sky-50 text-sky-700 ring-sky-600/15",
  shortlisted: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
  rejected:    "bg-rose-50 text-rose-700 ring-rose-600/15",
};
const STATUS_LABEL: Record<string, string> = {
  applied: "Applied", reviewed: "Under review", shortlisted: "Shortlisted", rejected: "Not selected",
};
// The candidate-visible journey, in order.
const STEPS = ["applied", "reviewed", "shortlisted"] as const;

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${STATUS_STYLE[status] ?? "bg-slate-100 text-slate-600 ring-slate-500/15"}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

export default function ApplicationsPage() {
  const { isLoading, user } = useRequireAuth("/login", "candidate");
  const toast = useToast();

  const [items,   setItems]   = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);
  const [busyId,  setBusyId]  = useState<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    applicationsApi.list()
      .then(r => setItems(Array.isArray(r) ? r : r.results ?? []))
      .catch(err => { setError(err); setItems([]); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (isLoading || user?.role !== "candidate") return;
    load();
  }, [isLoading, user, load]);

  async function withdraw(id: number) {
    setBusyId(id);
    try {
      await applicationsApi.withdraw(id);
      setItems(prev => prev.filter(a => a.id !== id));
      toast.success("Application withdrawn.");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setBusyId(null);
    }
  }

  if (isLoading || user?.role !== "candidate" || loading) {
    return (
      <div className="page">
        <div className="page-inner-sm space-y-3">
          <div className="skeleton h-10 w-48" />
          {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-24" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-inner-sm">

        {/* Header */}
        <div className="mb-7">
          <div className="flex items-center gap-2.5 mb-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-brand-100">
              <ClipboardList size={18} />
            </span>
            <h1 className="page-title">My Applications</h1>
          </div>
          <p className="muted">Track every role you&apos;ve applied to and where it stands.</p>
        </div>

        {error ? (
          <ErrorState variant="error" title="Couldn't load your applications"
            message={humanizeError(error)} onRetry={load} />
        ) : items.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-16 text-center">
            <div className="h-14 w-14 rounded-xl bg-slate-100 flex items-center justify-center mb-4 ring-1 ring-slate-200/70">
              <ClipboardList size={24} className="text-slate-400" />
            </div>
            <p className="font-medium text-slate-600">No applications yet</p>
            <p className="text-sm text-slate-500 mt-1 max-w-xs">Browse recommended roles and apply — they&apos;ll show up here.</p>
            <Link href="/recommended" className="btn-primary mt-5 !py-2.5 !px-5 !text-sm">
              <Send size={14} /> Find jobs
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-slate-500 tabular-nums">{items.length} application{items.length === 1 ? "" : "s"}</p>
            {items.map(app => {
              const job = app.job_detail;
              const rejected = app.status === "rejected";
              const stepIdx = STEPS.indexOf(app.status as typeof STEPS[number]);
              return (
                <div key={app.id} className="card p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3.5 min-w-0">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-100 to-brand-50 text-brand-700 font-bold text-sm">
                        {job?.company?.[0] ?? "?"}
                      </div>
                      <div className="min-w-0">
                        <Link href={`/jobs/${app.job}`} className="font-semibold text-slate-900 text-sm hover:text-brand-700 transition-colors">
                          {job?.title ?? `Job #${app.job}`}
                        </Link>
                        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 mt-0.5 text-xs text-slate-500">
                          {job?.company && <span>{job.company}</span>}
                          {job?.location && <span className="inline-flex items-center gap-1"><MapPin size={11} /> {job.location}</span>}
                          <span className="inline-flex items-center gap-1"><Clock size={11} /> {new Date(app.applied_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <StatusBadge status={app.status} />
                  </div>

                  {/* Progress steps */}
                  {!rejected && (
                    <div className="mt-4 flex items-center gap-1.5">
                      {STEPS.map((s, i) => (
                        <div key={s} className="flex-1">
                          <div className={`h-1.5 rounded-full ${i <= stepIdx ? "bg-brand-500" : "bg-slate-100"}`} />
                          <p className={`mt-1 text-2xs ${i <= stepIdx ? "text-slate-600 font-medium" : "text-slate-400"}`}>{STATUS_LABEL[s]}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="mt-4 flex items-center justify-between">
                    <Link href={`/jobs/${app.job}`} className="text-xs font-semibold text-brand-600 hover:text-brand-700 inline-flex items-center gap-1">
                      View job <ArrowRight size={12} />
                    </Link>
                    <button
                      onClick={() => withdraw(app.id)}
                      disabled={busyId === app.id}
                      className="text-xs font-medium text-slate-400 hover:text-red-600 transition-colors inline-flex items-center gap-1"
                    >
                      {busyId === app.id ? <Spinner size={12} /> : <Trash2 size={12} />} Withdraw
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
