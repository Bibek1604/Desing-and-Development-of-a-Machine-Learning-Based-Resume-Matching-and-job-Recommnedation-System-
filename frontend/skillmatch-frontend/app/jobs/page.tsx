"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { Search, SlidersHorizontal, ChevronDown, Briefcase, MapPin, Wallet } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  jobs as jobsApi, matching, applications as applicationsApi, feedback as feedbackApi,
  humanizeError, type Job, type JobMatch, type Application,
} from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import ErrorState from "@/components/ErrorState";
import PageHeader from "@/components/PageHeader";
import { JobCard, SkeletonCard, GapDrawer } from "@/components/jobs/JobCard";
import ApplyModal from "@/components/jobs/ApplyModal";

export default function AllJobsPage() {
  const { isAuthenticated, user } = useAuth();
  const isCandidate = !user?.role || user.role === "candidate";

  const [allJobs,    setAllJobs]    = useState<Job[]>([]);
  const [recMatches, setRecMatches] = useState<JobMatch[]>([]);
  const [search,     setSearch]     = useState("");
  const [jobType,    setJobType]    = useState("");
  const [location,   setLocation]   = useState("");
  const [minSalary,  setMinSalary]  = useState<string>("");
  const [page,       setPage]       = useState(1);
  const [total,      setTotal]      = useState(0);
  const [numPages,   setNumPages]   = useState(1);
  const [loading,    setLoading]    = useState(true);
  const [loadError,  setLoadError]  = useState<unknown>(null);
  const [gapJobId,   setGapJobId]   = useState<number | null>(null);
  const [appliedIds, setAppliedIds] = useState<Set<number>>(new Set());
  const [applyingId, setApplyingId] = useState<number | null>(null);
  const [applyFor,   setApplyFor]   = useState<Job | null>(null);   // Job the modal is currently open for
  const toast = useToast();

  const fetchAll = useCallback(() => {
    setLoading(true);
    setLoadError(null);
    const listPromise = jobsApi
      .list(search, jobType || undefined, page)
      .then(r => {
        const data = r as { results?: Job[]; count?: number; num_pages?: number };
        if (data && Array.isArray(data.results)) {
          setAllJobs(data.results);
          setTotal(data.count ?? data.results.length);
          setNumPages(data.num_pages ?? 1);
        } else {
          const arr = (r as Job[]) ?? [];
          setAllJobs(arr); setTotal(arr.length); setNumPages(1);
        }
      })
      .catch((err) => { setLoadError(err); setAllJobs([]); setTotal(0); setNumPages(1); });

    const promises: Promise<unknown>[] = [listPromise];
    // Pull recommendations only to annotate match scores on the cards.
    if (isAuthenticated && isCandidate) {
      promises.push(
        matching.recommendations().then(r => setRecMatches(r as JobMatch[])).catch(() => setRecMatches([])),
      );
    }
    Promise.all(promises).finally(() => setLoading(false));
  }, [search, jobType, page, isAuthenticated, isCandidate]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    if (!isAuthenticated || !isCandidate) return;
    applicationsApi.list()
      .then((r) => {
        const items: Application[] = Array.isArray(r) ? r : r.results ?? [];
        setAppliedIds(new Set(items.map((a) => a.job)));
      })
      .catch(() => {});
  }, [isAuthenticated, isCandidate]);

  // Instead of applying immediately, open the ApplyModal so the candidate
  // can supply an optional cover note. The actual POST happens in
  // `submitApplication` once they hit Submit in the modal.
  function openApply(jobId: number) {
    const job = allJobs.find((j) => j.id === jobId);
    if (job) setApplyFor(job);
  }

  async function submitApplication(coverNote: string) {
    if (!applyFor) return;
    setApplyingId(applyFor.id);
    try {
      await applicationsApi.create(applyFor.id, coverNote);
      setAppliedIds((prev) => new Set(prev).add(applyFor.id));
      toast.success("Application submitted!");
      setApplyFor(null);
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setApplyingId(null);
    }
  }

  async function handleFeedback(jobId: number, signal: "up" | "down", score: number) {
    try {
      await feedbackApi.send(jobId, signal, score);
      toast.success(signal === "up" ? "Thanks — noted." : "Thanks — we'll show fewer like this.");
    } catch (err) {
      toast.error(humanizeError(err));
    }
  }

  const recJobMap = new Map(recMatches.map(m => [m.job.id, m]));

  // Client-side location + salary filter. Backend `search` handles keyword +
  // job_type; the extra filters run over the current page result set. This
  // is intentional — it keeps the current server contract stable while still
  // giving candidates finer control on the visible list.
  const filteredJobs = useMemo(() => {
    const loc = location.trim().toLowerCase();
    const minS = minSalary ? parseInt(minSalary, 10) * 1000 : 0;
    return allJobs.filter((j) => {
      if (loc && !(j.location ?? "").toLowerCase().includes(loc)) return false;
      if (minS > 0) {
        const jobMin = j.salary_min ?? 0;
        const jobMax = j.salary_max ?? jobMin;
        if (Math.max(jobMin, jobMax) < minS) return false;
      }
      return true;
    });
  }, [allJobs, location, minSalary]);

  const renderCard = (job: Job) => {
    const match = recJobMap.get(job.id);
    return (
      <JobCard
        key={job.id}
        job={job}
        score={match?.score}
        matchedSkills={match?.matched_skills}
        onViewGap={isAuthenticated && isCandidate ? setGapJobId : undefined}
        onApply={isAuthenticated && isCandidate ? openApply : undefined}
        onFeedback={isAuthenticated && isCandidate ? handleFeedback : undefined}
        applied={appliedIds.has(job.id)}
        applying={applyingId === job.id}
      />
    );
  };

  return (
    <div className="page">
      <div className="page-inner-md">
        <PageHeader
          icon={Briefcase}
          eyebrow="Opportunities"
          title="All Jobs"
          subtitle="Browse every open position across Nepal's tech sector"
        />

        {/* Search + filters */}
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <div className="relative flex-1 min-w-48">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search jobs, skills, companies…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              onKeyDown={e => e.key === "Enter" && fetchAll()}
              className="input pl-9"
              aria-label="Search jobs"
            />
          </div>
          <div className="relative">
            <SlidersHorizontal size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
            <select
              value={jobType}
              onChange={e => { setJobType(e.target.value); setPage(1); }}
              className="input pl-8 pr-9 appearance-none cursor-pointer"
              aria-label="Filter by job type"
            >
              <option value="">All types</option>
              <option value="full_time">Full Time</option>
              <option value="part_time">Part Time</option>
              <option value="internship">Internship</option>
              <option value="contract">Contract</option>
              <option value="remote">Remote</option>
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 mb-5">
          <div className="relative flex-1 min-w-44">
            <MapPin size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Location — e.g. Kathmandu, Lalitpur…"
              value={location}
              onChange={e => setLocation(e.target.value)}
              className="input pl-9"
              aria-label="Filter by location"
            />
          </div>
          <div className="relative w-full sm:w-56">
            <Wallet size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="number"
              min={0}
              step={5}
              placeholder="Min salary (NPR ×1000)"
              value={minSalary}
              onChange={e => setMinSalary(e.target.value)}
              className="input pl-9 tabular-nums"
              aria-label="Minimum salary in NPR thousands"
            />
          </div>
          {(location || minSalary) && (
            <button
              type="button"
              onClick={() => { setLocation(""); setMinSalary(""); }}
              className="text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>

        {!loading && !loadError && (
          <p className="text-sm text-slate-500 mb-4 tabular-nums">
            {filteredJobs.length} of {total} {total === 1 ? "role" : "roles"} shown
          </p>
        )}

        {loading ? (
          <div className="grid md:grid-cols-2 gap-4">
            {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : loadError ? (
          <ErrorState variant="error" title="Couldn't load jobs" message={humanizeError(loadError)} onRetry={fetchAll} />
        ) : filteredJobs.length === 0 ? (
          <div className="card flex flex-col items-center justify-center py-20 text-center">
            <div className="h-14 w-14 rounded-xl bg-slate-100 flex items-center justify-center mb-4 ring-1 ring-slate-200/70">
              <Search size={24} className="text-slate-400" />
            </div>
            <p className="font-medium text-slate-600">No jobs found</p>
            <p className="text-sm text-slate-500 mt-1 max-w-xs">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {filteredJobs.map(renderCard)}
          </div>
        )}

        {/* Pagination */}
        {!loading && !loadError && numPages > 1 && (
          <div className="mt-8 flex items-center justify-center gap-3">
            <button disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}
              className="btn-outline !py-2 !px-3.5 !text-sm disabled:opacity-40">
              <ChevronDown size={15} className="rotate-90" /> Prev
            </button>
            <span className="text-sm text-slate-500 tabular-nums">Page {page} of {numPages}</span>
            <button disabled={page >= numPages} onClick={() => setPage(p => Math.min(numPages, p + 1))}
              className="btn-outline !py-2 !px-3.5 !text-sm disabled:opacity-40">
              Next <ChevronDown size={15} className="-rotate-90" />
            </button>
          </div>
        )}
      </div>

      <GapDrawer jobId={gapJobId} onClose={() => setGapJobId(null)} />
      <ApplyModal
        job={applyFor}
        submitting={applyingId === applyFor?.id}
        onCancel={() => setApplyFor(null)}
        onSubmit={submitApplication}
      />
    </div>
  );
}
