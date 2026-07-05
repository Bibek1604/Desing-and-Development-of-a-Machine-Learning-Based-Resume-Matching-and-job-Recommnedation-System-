"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, MapPin, Clock, Send, Check, Building2,
  Wallet, Sparkles, TrendingUp, X as XIcon, CheckCircle2,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  jobs as jobsApi, applications as applicationsApi, matching,
  humanizeError, type Job, type Application, type ExplainMatch,
} from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import ErrorState from "@/components/ErrorState";
import Spinner from "@/components/Spinner";
import CompanyLogo from "@/components/CompanyLogo";
import ApplyModal from "@/components/jobs/ApplyModal";
import { scoreBadgeClass } from "@/lib/score";

const JOB_TYPE_COLORS: Record<string, string> = {
  full_time:  "bg-emerald-50 text-emerald-700 ring-emerald-600/10",
  part_time:  "bg-amber-50 text-amber-700 ring-amber-600/10",
  internship: "bg-brand-50 text-brand-700 ring-brand-600/10",
  contract:   "bg-orange-50 text-orange-700 ring-orange-600/10",
  remote:     "bg-sky-50 text-sky-700 ring-sky-600/10",
};

function salaryLabel(job: Job): string | null {
  if (job.salary_min) {
    const min = `NPR ${(job.salary_min / 1000).toFixed(0)}k`;
    return job.salary_max ? `${min}–${(job.salary_max / 1000).toFixed(0)}k / month` : `${min}+ / month`;
  }
  return job.salary_text ?? null;
}

export default function JobDetailPage() {
  const params = useParams();
  const jobId = Number(params?.id);
  const { isAuthenticated, user } = useAuth();
  const isCandidate = isAuthenticated && (!user?.role || user.role === "candidate");
  const toast = useToast();

  const [job,     setJob]     = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);

  const [applied,   setApplied]   = useState(false);
  const [applying,  setApplying]  = useState(false);
  const [match,     setMatch]     = useState<ExplainMatch | null>(null);
  const [applyOpen, setApplyOpen] = useState(false);

  const load = useCallback(() => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    jobsApi.get(jobId)
      .then(setJob)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [jobId]);

  useEffect(() => { load(); }, [load]);

  // Candidate-only extras: applied state + match explanation (best-effort).
  useEffect(() => {
    if (!isCandidate || !jobId) return;
    applicationsApi.list()
      .then(r => {
        const items: Application[] = Array.isArray(r) ? r : r.results ?? [];
        setApplied(items.some(a => a.job === jobId));
      })
      .catch(() => {});
    matching.explain(jobId)
      .then(setMatch)
      .catch(() => setMatch(null));
  }, [isCandidate, jobId]);

  async function submitApplication(coverNote: string) {
    setApplying(true);
    try {
      await applicationsApi.create(jobId, coverNote);
      setApplied(true);
      setApplyOpen(false);
      toast.success("Application submitted!");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setApplying(false);
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="page-inner-sm space-y-5">
          <div className="skeleton h-6 w-24" />
          <div className="skeleton h-32" />
          <div className="skeleton h-64" />
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="page">
        <div className="page-inner-sm">
          <ErrorState
            variant="error"
            title="Couldn't load this job"
            message={error ? humanizeError(error) : "This job posting doesn't exist or has been removed."}
            onRetry={load}
            actionHref="/jobs"
            actionLabel="Back to jobs"
          />
        </div>
      </div>
    );
  }

  const badgeClass = JOB_TYPE_COLORS[job.job_type] ?? "bg-slate-50 text-slate-600 ring-slate-500/10";
  const salary = salaryLabel(job);
  const skills = job.required_skills ?? [];

  return (
    <div className="page">
      <div className="page-inner-sm space-y-6">

        <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors">
          <ArrowLeft size={15} /> Back to jobs
        </Link>

        {/* Header */}
        <div className="card p-6 sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 min-w-0">
              <CompanyLogo name={job.company} src={job.company_logo} size={56} className="!rounded-xl" />
              <div className="min-w-0">
                <h1 className="page-title">{job.title}</h1>
                <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
                  <span className="inline-flex items-center gap-1"><Building2 size={13} /> {job.company || "Company"}</span>
                  {job.location && <span className="inline-flex items-center gap-1"><MapPin size={13} /> {job.location}</span>}
                  {job.created_at && (
                    <span className="inline-flex items-center gap-1">
                      <Clock size={13} /> {new Date(job.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </span>
                  )}
                </div>
              </div>
            </div>
            {match && <span className={`${scoreBadgeClass(match.score)} shrink-0`}>{match.score}% match</span>}
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${badgeClass}`}>
              {job.job_type_display ?? job.job_type?.replace("_", " ")}
            </span>
            {salary && (
              <span className="inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium tabular-nums bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-500/10">
                <Wallet size={12} /> {salary}
              </span>
            )}
            {!job.is_active && (
              <span className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-500/10">
                Closed
              </span>
            )}
          </div>

          {/* Apply */}
          <div className="mt-6 flex items-center gap-3">
            {isCandidate ? (
              applied ? (
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 px-4 py-2.5 text-sm font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-600/15">
                  <Check size={15} /> Applied
                </span>
              ) : (
                <button onClick={() => setApplyOpen(true)} disabled={applying || !job.is_active} className="btn-primary !py-2.5 !px-6">
                  {applying ? <><Spinner size={15} /> Applying…</> : <><Send size={15} /> Apply now</>}
                </button>
              )
            ) : !isAuthenticated ? (
              <Link href="/login" className="btn-primary !py-2.5 !px-6"><Send size={15} /> Sign in to apply</Link>
            ) : null}
          </div>
        </div>

        {/* Match insight (candidates) */}
        {match && (match.matched_skills?.length || match.missing_skills?.length || match.explanation_summary) ? (
          <div className="card p-6 space-y-4">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600"><Sparkles size={15} /></span>
              <h2 className="subheading">Why this matches you</h2>
            </div>
            {match.explanation_summary && <p className="text-sm text-slate-600 leading-relaxed">{match.explanation_summary}</p>}
            {match.matched_skills?.length > 0 && (
              <div>
                <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.06em] text-emerald-700 mb-2"><CheckCircle2 size={12} /> Skills you have</p>
                <div className="flex flex-wrap gap-1.5">{match.matched_skills.map((s, i) => <span key={i} className="chip-green text-2xs">{s}</span>)}</div>
              </div>
            )}
            {match.missing_skills?.length > 0 && (
              <div>
                <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.06em] text-amber-700 mb-2"><XIcon size={12} /> Skills to grow</p>
                <div className="flex flex-wrap gap-1.5">{match.missing_skills.map((s, i) => <span key={i} className="chip-amber text-2xs">{s}</span>)}</div>
              </div>
            )}
          </div>
        ) : null}

        {/* Description */}
        <div className="card p-6 sm:p-7">
          <h2 className="subheading mb-3">Job Description</h2>
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{job.description || "No description provided."}</p>
        </div>

        {/* Requirements */}
        {job.requirements && (
          <div className="card p-6 sm:p-7">
            <h2 className="subheading mb-3">Requirements</h2>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">{job.requirements}</p>
          </div>
        )}

        {/* Required skills */}
        {skills.length > 0 && (
          <div className="card p-6 sm:p-7">
            <h2 className="subheading mb-3 flex items-center gap-2"><TrendingUp size={16} className="text-brand-600" /> Required Skills</h2>
            <div className="flex flex-wrap gap-1.5">
              {skills.map(s => <span key={s.id} className="chip text-2xs">{s.name}</span>)}
            </div>
          </div>
        )}

        {/* Bottom apply for convenience */}
        {isCandidate && !applied && job.is_active && (
          <div className="flex justify-end">
            <button onClick={() => setApplyOpen(true)} disabled={applying} className="btn-primary !py-2.5 !px-6">
              {applying ? <><Spinner size={15} /> Applying…</> : <><Send size={15} /> Apply now</>}
            </button>
          </div>
        )}
      </div>

      <ApplyModal
        job={applyOpen ? job : null}
        submitting={applying}
        onCancel={() => setApplyOpen(false)}
        onSubmit={submitApplication}
      />
    </div>
  );
}
