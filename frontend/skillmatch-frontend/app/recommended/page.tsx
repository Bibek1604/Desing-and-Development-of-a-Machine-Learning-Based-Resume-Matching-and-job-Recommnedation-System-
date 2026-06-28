"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Zap } from "lucide-react";
import { useRequireAuth } from "@/context/AuthContext";
import {
  matching, applications as applicationsApi, feedback as feedbackApi,
  humanizeError, type JobMatch, type Application,
} from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import ErrorState from "@/components/ErrorState";
import PageHeader from "@/components/PageHeader";
import { JobCard, SkeletonCard, GapDrawer } from "@/components/jobs/JobCard";

const REC_THRESHOLD = 70;

export default function RecommendedPage() {
  const { isLoading, user } = useRequireAuth("/login", "candidate");
  const toast = useToast();

  const [matches,    setMatches]    = useState<JobMatch[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<unknown>(null);
  const [gapJobId,   setGapJobId]   = useState<number | null>(null);
  const [appliedIds, setAppliedIds] = useState<Set<number>>(new Set());
  const [applyingId, setApplyingId] = useState<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    matching.recommendations()
      .then(r => setMatches(r as JobMatch[]))
      .catch(err => { setError(err); setMatches([]); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (isLoading || user?.role !== "candidate") return;
    load();
    applicationsApi.list()
      .then(r => {
        const items: Application[] = Array.isArray(r) ? r : r.results ?? [];
        setAppliedIds(new Set(items.map(a => a.job)));
      })
      .catch(() => {});
  }, [isLoading, user, load]);

  async function handleApply(jobId: number) {
    setApplyingId(jobId);
    try {
      await applicationsApi.create(jobId);
      setAppliedIds(prev => new Set(prev).add(jobId));
      toast.success("Application submitted!");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setApplyingId(null);
    }
  }

  async function handleFeedback(jobId: number, signal: "up" | "down", score: number) {
    try {
      await feedbackApi.send(jobId, signal, score);
      toast.success(signal === "up"
        ? "Thanks — we'll surface more roles like this."
        : "Thanks — we'll show fewer like this.");
    } catch (err) {
      toast.error(humanizeError(err));
    }
  }

  const strong = matches.filter(m => (m.score ?? 0) >= REC_THRESHOLD);

  if (isLoading || user?.role !== "candidate") {
    return (
      <div className="page"><div className="page-inner-md grid md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
      </div></div>
    );
  }

  return (
    <div className="page">
      <div className="page-inner-md">
        <PageHeader
          icon={Zap}
          eyebrow="For you"
          title="Recommended"
          subtitle="Strong matches (70%+) against the resume in your profile"
        />

        {loading ? (
          <div className="grid md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : error ? (
          <ErrorState variant="error" title="Couldn't load recommendations" message={humanizeError(error)} onRetry={load} />
        ) : strong.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-16 text-center">
            <div className="h-14 w-14 rounded-xl bg-slate-100 flex items-center justify-center mb-4 ring-1 ring-slate-200/70">
              <Zap size={24} className="text-slate-400" />
            </div>
            <p className="font-medium text-slate-600">No strong matches yet</p>
            <p className="text-sm text-slate-500 mt-1 max-w-sm">
              We only show roles matching 70%+. Add skills to your profile or upload your CV to raise your matches — meanwhile, browse every role on the All Jobs page.
            </p>
            <div className="mt-5 flex gap-3">
              <Link href="/profile" className="btn-outline !py-2 !text-xs !px-4">Update profile</Link>
              <Link href="/jobs" className="btn-primary !py-2 !text-xs !px-4">Browse all jobs</Link>
            </div>
          </div>
        ) : (
          <>
            <p className="text-sm text-slate-500 mb-4 tabular-nums">{strong.length} strong {strong.length === 1 ? "match" : "matches"}</p>
            <div className="grid md:grid-cols-2 gap-4">
              {strong.map(m => (
                <JobCard
                  key={m.job.id}
                  job={m.job}
                  score={m.score}
                  matchedSkills={m.matched_skills}
                  onViewGap={setGapJobId}
                  onApply={handleApply}
                  onFeedback={handleFeedback}
                  applied={appliedIds.has(m.job.id)}
                  applying={applyingId === m.job.id}
                />
              ))}
            </div>
          </>
        )}
      </div>

      <GapDrawer jobId={gapJobId} onClose={() => setGapJobId(null)} />
    </div>
  );
}
