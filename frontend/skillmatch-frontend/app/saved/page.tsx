"use client";

import { useCallback, useEffect, useState } from "react";
import { Bookmark } from "lucide-react";
import { useRequireAuth } from "@/context/AuthContext";
import {
  savedJobs as savedApi, humanizeError, type SavedJob,
} from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import ErrorState from "@/components/ErrorState";
import { JobCard, SkeletonCard } from "@/components/jobs/JobCard";
import { useToast } from "@/context/ToastContext";

export default function SavedJobsPage() {
  const { isLoading: authLoading } = useRequireAuth("/login", "candidate");
  const toast = useToast();

  const [items,   setItems]   = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    savedApi.list()
      .then((r) => {
        const list = Array.isArray(r) ? r : r.results ?? [];
        setItems(list);
      })
      .catch((err) => { setError(err); setItems([]); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!authLoading) load();
  }, [authLoading, load]);

  async function handleUnsave(jobId: number) {
    const row = items.find((s) => s.job === jobId);
    if (!row) return;
    // Optimistic remove — restore on failure.
    const prev = items;
    setItems(items.filter((s) => s.id !== row.id));
    try {
      await savedApi.unsave(row.id);
      toast.success("Removed from saved");
    } catch (err) {
      setItems(prev);
      toast.error(humanizeError(err));
    }
  }

  if (authLoading) {
    return (
      <div className="page">
        <div className="page-inner-md">
          <div className="skeleton h-8 w-40 mb-6" />
          <div className="grid md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-inner-md">
        <PageHeader
          icon={Bookmark}
          eyebrow="Bookmarks"
          title="Saved Jobs"
          subtitle="Jobs you've saved to come back to later"
        />

        {loading ? (
          <div className="grid md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : error ? (
          <ErrorState
            variant="error"
            title="Couldn't load saved jobs"
            message={humanizeError(error)}
            onRetry={load}
          />
        ) : items.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-20 text-center">
            <div className="h-14 w-14 rounded-xl bg-slate-100 flex items-center justify-center mb-4 ring-1 ring-slate-200/70">
              <Bookmark size={24} className="text-slate-400" />
            </div>
            <p className="font-medium text-slate-600">No saved jobs yet</p>
            <p className="text-sm text-slate-500 mt-1 max-w-xs">
              Tap the bookmark icon on any job card to save it here.
            </p>
          </div>
        ) : (
          <>
            <p className="text-sm text-slate-500 mb-4 tabular-nums">
              {items.length} {items.length === 1 ? "job" : "jobs"} saved
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              {items.map((s) => (
                s.job_detail ? (
                  <JobCard
                    key={s.id}
                    job={s.job_detail}
                    saved
                    onToggleSave={handleUnsave}
                  />
                ) : null
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
