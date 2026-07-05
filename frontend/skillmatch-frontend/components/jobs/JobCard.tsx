"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  X, TrendingUp, MapPin, Clock, Check, Wrench, ScrollText, CalendarDays, Send,
  ThumbsUp, ThumbsDown, Bookmark,
} from "lucide-react";
import { matching, humanizeError, type Job } from "@/lib/api";
import Spinner from "@/components/Spinner";
import CompanyLogo from "@/components/CompanyLogo";
import { scoreBadgeClass } from "@/lib/score";

export function SkeletonCard() {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex justify-between">
        <div className="skeleton h-4 w-2/3" />
        <div className="skeleton h-6 w-14" />
      </div>
      <div className="skeleton h-3 w-1/2" />
      <div className="flex gap-2">
        {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-5 w-16 !rounded-md" />)}
      </div>
      <div className="skeleton h-3 w-full" />
      <div className="skeleton h-3 w-4/5" />
    </div>
  );
}

const JOB_TYPE_COLORS: Record<string, string> = {
  full_time:  "bg-emerald-50 text-emerald-700 ring-emerald-600/10",
  part_time:  "bg-amber-50 text-amber-700 ring-amber-600/10",
  internship: "bg-brand-50 text-brand-700 ring-brand-600/10",
  contract:   "bg-orange-50 text-orange-700 ring-orange-600/10",
  remote:     "bg-sky-50 text-sky-700 ring-sky-600/10",
};

export interface JobCardProps {
  job: Job;
  score?: number;
  matchedSkills?: string[];
  onViewGap?: (jobId: number) => void;
  onApply?: (jobId: number) => void;
  onFeedback?: (jobId: number, signal: "up" | "down", score: number) => void;
  onToggleSave?: (jobId: number) => void;
  saved?: boolean;
  applied?: boolean;
  applying?: boolean;
}

export function JobCard({
  job, score, matchedSkills, onViewGap, onApply, onFeedback, onToggleSave,
  saved, applied, applying,
}: JobCardProps) {
  const [fb, setFb] = useState<"up" | "down" | null>(null);
  function sendFb(signal: "up" | "down") {
    setFb(signal);
    onFeedback?.(job.id, signal, score ?? 0);
  }
  const badgeClass = JOB_TYPE_COLORS[job.job_type] ?? "bg-slate-50 text-slate-600 ring-slate-500/10";

  return (
    <div className="card-hover p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <CompanyLogo name={job.company} src={job.company_logo} size={40} />
          <div className="min-w-0">
            <h3 className="font-semibold text-slate-900 text-sm truncate">
              <Link href={`/jobs/${job.id}`} className="hover:text-brand-700 transition-colors">{job.title}</Link>
            </h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <p className="text-xs text-slate-500 truncate">{job.company}</p>
              <span className="text-slate-300">·</span>
              <div className="flex items-center gap-1 text-xs text-slate-500 shrink-0">
                <MapPin size={10} /> {job.location}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {onToggleSave && (
            <button
              type="button"
              onClick={() => onToggleSave(job.id)}
              aria-label={saved ? "Remove from saved jobs" : "Save this job"}
              className={`p-1 rounded transition-colors ${saved ? "text-brand-600" : "text-slate-400 hover:text-brand-600"}`}
              title={saved ? "Saved" : "Save for later"}
            >
              <Bookmark size={14} fill={saved ? "currentColor" : "none"} />
            </button>
          )}
          {score != null && <span className={scoreBadgeClass(score)}>{score}%</span>}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-2xs font-semibold capitalize ring-1 ring-inset ${badgeClass}`}>
          {job.job_type_display ?? job.job_type?.replace("_", " ")}
        </span>
        {(job.salary_min || job.salary_text) && (
          <span className="inline-flex items-center rounded-md px-2 py-0.5 text-2xs font-medium tabular-nums bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-500/10">
            {job.salary_min
              ? `NPR ${(job.salary_min / 1000).toFixed(0)}k${job.salary_max ? `–${(job.salary_max / 1000).toFixed(0)}k` : "+"}`
              : job.salary_text}
          </span>
        )}
        <span className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-2xs text-slate-500 bg-slate-50 ring-1 ring-inset ring-slate-500/10">
          <Clock size={9} />
          {new Date(job.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
        </span>
      </div>

      {matchedSkills && matchedSkills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {matchedSkills.slice(0, 5).map((s, i) => (
            <span key={i} className="chip text-2xs">{s}</span>
          ))}
          {matchedSkills.length > 5 && (
            <span className="text-2xs font-medium text-slate-400 self-center">
              +{matchedSkills.length - 5} more
            </span>
          )}
        </div>
      )}

      <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{job.description}</p>

      <div className="flex items-center justify-between gap-3 pt-1">
        <div className="flex items-center gap-3">
          <Link
            href={`/jobs/${job.id}`}
            className="text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors duration-150"
          >
            View details
          </Link>
          {onFeedback && score != null && (
            <span className="flex items-center gap-0.5" title="Is this a good match?">
              <button type="button" onClick={() => sendFb("up")} aria-label="Relevant"
                className={`p-1 rounded transition-colors ${fb === "up" ? "text-emerald-600" : "text-slate-400 hover:text-emerald-600"}`}>
                <ThumbsUp size={13} />
              </button>
              <button type="button" onClick={() => sendFb("down")} aria-label="Not relevant"
                className={`p-1 rounded transition-colors ${fb === "down" ? "text-red-500" : "text-slate-400 hover:text-red-500"}`}>
                <ThumbsDown size={13} />
              </button>
            </span>
          )}
        </div>
        {(onApply || onViewGap) && (
          <div className="flex items-center gap-3">
            {onViewGap && (
              <button
                onClick={() => onViewGap(job.id)}
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors duration-150 flex items-center gap-1"
              >
                <TrendingUp size={12} /> Skill gap
              </button>
            )}
            {onApply && (
              applied ? (
                <span className="chip-green gap-1 !py-1"><Check size={11} /> Applied</span>
              ) : (
                <button
                  onClick={() => onApply(job.id)}
                  disabled={applying}
                  className="btn-primary !py-1.5 !px-3.5 !text-xs"
                >
                  {applying ? <Spinner size={12} /> : <Send size={11} />}
                  {applying ? "Applying…" : "Apply"}
                </button>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function GapSection({
  icon: Icon, title, items, chipClass,
}: {
  icon: React.ElementType; title: string; items: string[]; chipClass: string;
}) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="flex items-center gap-1.5 text-xs font-bold text-slate-700 uppercase tracking-[0.06em] mb-2">
        <Icon size={12} className="text-slate-400" /> {title}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={chipClass}>{item}</span>
        ))}
      </div>
    </div>
  );
}

export function GapDrawer({ jobId, onClose }: { jobId: number | null; onClose: () => void }) {
  const [gap, setGap] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);
    setGap(null);
    matching.skillGap(jobId)
      .then(setGap)
      .catch((err) => setGap({ error: humanizeError(err) }))
      .finally(() => setLoading(false));
  }, [jobId]);

  if (!jobId) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative z-50 w-full max-w-md bg-white h-full overflow-y-auto shadow-pop animate-slide-in-right">
        <div className="sticky top-0 bg-white/95 backdrop-blur border-b border-slate-100 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="font-semibold tracking-[-0.01em] text-slate-900">Skill Gap Analysis</h2>
            <p className="text-xs text-slate-500 mt-0.5">What you need to close the gap</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close skill gap panel"
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors duration-150"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="skeleton h-10" />
              ))}
            </div>
          )}

          {gap && !loading && (
            <>
              {gap.error ? (
                <p className="text-red-600 text-sm">{gap.error as string}</p>
              ) : (
                <div className="space-y-5">
                  {(gap.match_improvement_pct as number) > 0 && (
                    <div className="flex items-center gap-2.5 rounded-lg border border-brand-100 bg-brand-50/70 p-3.5">
                      <TrendingUp size={16} className="text-brand-600 shrink-0" />
                      <p className="text-sm text-brand-800">
                        You can improve your match by{" "}
                        <span className="font-bold text-brand-600">+{gap.match_improvement_pct as number}%</span>
                      </p>
                    </div>
                  )}
                  <GapSection icon={Check}        title="Matched Skills"   items={gap.matched_skills as string[]}         chipClass="chip-green" />
                  <GapSection icon={X}            title="Missing Skills"   items={gap.missing_skills as string[]}         chipClass="chip-red" />
                  <GapSection icon={Wrench}       title="Missing Tech"     items={gap.missing_technologies as string[]}   chipClass="chip-amber" />
                  <GapSection icon={ScrollText}   title="Certifications"   items={gap.missing_certifications as string[]} chipClass="chip" />
                  {(gap.experience_gaps as string[])?.length > 0 && (
                    <div>
                      <p className="flex items-center gap-1.5 text-xs font-bold text-slate-700 uppercase tracking-[0.06em] mb-2">
                        <CalendarDays size={12} className="text-slate-400" /> Experience Gaps
                      </p>
                      <ul className="space-y-1.5">
                        {(gap.experience_gaps as string[]).map((g, i) => (
                          <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-slate-400 shrink-0" />
                            {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
