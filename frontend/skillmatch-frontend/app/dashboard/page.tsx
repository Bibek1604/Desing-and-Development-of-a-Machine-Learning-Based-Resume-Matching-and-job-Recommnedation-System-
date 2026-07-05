"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp, FileText, GraduationCap, Sparkles,
  Brain, ArrowRight, Target, ChevronRight,
  Zap, ClipboardList, UserCog, Upload,
} from "lucide-react";
import { useRequireAuth } from "@/context/AuthContext";
import { matching, mediaUrl, humanizeError, APIError, type DashboardData } from "@/lib/api";
import ErrorState from "@/components/ErrorState";
import Avatar from "@/components/Avatar";
import EmailVerifyBanner from "@/components/EmailVerifyBanner";
import { scoreTextClass, scoreBarClass, scoreBadgeClass } from "@/lib/score";

function QuickAction({ href, icon: Icon, label, hint }: {
  href: string; icon: typeof Zap; label: string; hint: string;
}) {
  return (
    <Link href={href} className="group card-hover p-4 flex items-center gap-3">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 transition-colors group-hover:bg-brand-600 group-hover:text-white">
        <Icon size={17} />
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-slate-900 truncate">{label}</p>
        <p className="text-2xs text-slate-500 truncate">{hint}</p>
      </div>
    </Link>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({
  label, value, sub, icon, color,
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ReactNode; color: string;
}) {
  return (
    <div className="card relative overflow-hidden p-5 flex items-start gap-3.5 transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lift">
      <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${color}`}>
        {icon}
      </span>
      <div className="min-w-0">
        <p className="text-2xs font-semibold text-slate-500 uppercase tracking-[0.08em]">{label}</p>
        <p className="mt-0.5 page-title tabular-nums">{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}

function ScoreBar({ label, value, color = "bg-brand-500" }: {
  label: string; value: number; color?: string;
}) {
  const clamp = Math.min(100, Math.max(0, value));
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="font-medium text-slate-600">{label}</span>
        <span className="font-semibold text-slate-800 tabular-nums">{Math.round(clamp)}</span>
      </div>
      <div className="progress-track">
        <div className={`progress-fill ${color}`} style={{ width: `${clamp}%` }} />
      </div>
    </div>
  );
}

function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  // Candidate home — employers/admins are redirected to their own area.
  const { isLoading: authLoading, isAuthenticated, user } = useRequireAuth("/login", "candidate");
  const [data,    setData]    = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    matching.dashboard()
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (authLoading || !isAuthenticated || user?.role !== "candidate") return;
    load();
  }, [authLoading, isAuthenticated, user, load]);

  if (authLoading || loading || (user && user.role !== "candidate")) {
    return (
      <div className="page">
        <div className="page-inner space-y-6">
          <Skeleton className="h-28 w-full" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
          </div>
          <div className="grid md:grid-cols-2 gap-5">
            <Skeleton className="h-72" />
            <Skeleton className="h-72" />
          </div>
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  // Only a genuine "can't reach the server" error blocks the page. Any other
  // failure (e.g. a brand-new account with no resume yet, or a transient ML
  // hiccup) degrades to the normal dashboard with empty states + a soft notice
  // — we never throw the user out of their dashboard.
  if (error instanceof APIError && error.isNetworkError) {
    return (
      <div className="page">
        <div className="page-inner-sm">
          <ErrorState
            variant="network"
            title="Couldn't reach the server"
            message={humanizeError(error)}
            onRetry={load}
          />
        </div>
      </div>
    );
  }
  const softNotice = error ? humanizeError(error) : null;

  const profile  = data?.profile;
  const ats      = data?.ats_analysis;
  const career   = data?.career_recommendations;
  const topJobs  = data?.top_job_matches ?? [];

  const atsScore      = ats?.ats_score ?? 0;
  const atsScoreColor = scoreTextClass(atsScore);
  const atsBarColor   = scoreBarClass(atsScore);

  return (
    <div className="page">
      <div className="page-inner space-y-6">

        <EmailVerifyBanner />

        {/* ── Hero header ── */}
        <div className="card overflow-hidden">
          <div className="relative bg-gradient-aurora px-6 py-7 sm:px-8">
            <div className="absolute inset-0 bg-grid opacity-15" />
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
            <div className="relative flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 min-w-0">
                <Avatar
                  name={user?.full_name || profile?.full_name}
                  src={profile?.avatar ?? null}
                  size={56}
                  className="ring-2 ring-white/25 shadow-sm"
                />
                <div className="min-w-0">
                  <p className="text-brand-100/80 text-sm font-medium mb-1 truncate">
                    {career?.top_role ? `Top career match: ${career.top_role}` : "Welcome to your dashboard"}
                  </p>
                  <h1 className="text-2xl font-bold tracking-[-0.02em] text-white truncate">
                    {profile?.full_name
                      ? `Hey, ${profile.full_name.split(" ")[0]}!`
                      : "Your Dashboard"}
                  </h1>
                  <p className="text-brand-100/70 text-sm mt-1 truncate">
                    {profile?.university || "Complete your profile to get started"}
                  </p>
                </div>
              </div>
              <Link
                href="/dashboard/ai-insights"
                className="hidden sm:flex shrink-0 items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white backdrop-blur-sm transition-colors duration-150 hover:bg-white/20"
              >
                <Brain size={15} />
                AI Insights
                <ChevronRight size={14} className="opacity-60" />
              </Link>
            </div>
          </div>
        </div>

        {softNotice && (
          <div className="flex items-start gap-2.5 rounded-lg border border-amber-200/70 bg-amber-50 p-3.5 text-sm text-amber-800" role="status">
            <Sparkles size={15} className="mt-0.5 shrink-0 text-amber-500" />
            <span>Some insights couldn&apos;t load just now, so a few panels may be empty — your dashboard still works. Upload your CV to populate it.</span>
          </div>
        )}

        {/* ── Quick actions ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <QuickAction href="/recommended"      icon={Zap}          label="Recommended"  hint="Jobs matched to you" />
          <QuickAction href="/applications"      icon={ClipboardList} label="Applications"  hint="Track your applies" />
          <QuickAction href="/profile"           icon={UserCog}     label="Edit profile" hint="Skills & preferences" />
          <QuickAction href="/profile"           icon={Upload}      label="Upload CV"    hint="Refresh your matches" />
        </div>

        {/* ── Stat cards ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            label="ATS Score"
            value={ats ? atsScore : "—"}
            sub={ats ? "Resume quality" : "No resume yet"}
            icon={<FileText size={18} />}
            color="bg-brand-50 text-brand-600"
          />
          <StatCard
            label="Skills"
            value={profile?.skills_count ?? "—"}
            sub="Extracted from CV"
            icon={<Target size={18} />}
            color="bg-accent-50 text-accent-600"
          />
          <StatCard
            label="CGPA"
            value={profile?.cgpa ?? "—"}
            sub={profile?.degree ?? "Degree"}
            icon={<GraduationCap size={18} />}
            color="bg-violet-50 text-violet-600"
          />
          <StatCard
            label="Hire Score"
            value={
              profile?.hiring_probability != null
                ? `${Math.round((profile.hiring_probability as number) * 100)}%`
                : "—"
            }
            sub="AI estimate"
            icon={<TrendingUp size={18} />}
            color="bg-emerald-50 text-emerald-600"
          />
        </div>

        {/* ── ATS + Career panels ── */}
        <div className="grid md:grid-cols-2 gap-5">

          {/* ATS */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="subheading">Resume Quality</h2>
                <p className="text-xs text-slate-500 mt-0.5">ATS analysis breakdown</p>
              </div>
              {ats && (
                <div className="text-right">
                  <span className={`text-2xl font-bold tabular-nums tracking-[-0.02em] ${atsScoreColor}`}>
                    {atsScore}
                  </span>
                  <span className="text-slate-400 text-sm">/100</span>
                </div>
              )}
            </div>

            {ats ? (
              <div className="space-y-3.5">
                <ScoreBar label="Completeness" value={ats.completeness_score ?? 0} color={atsBarColor} />
                <ScoreBar label="Keywords"     value={ats.keyword_score     ?? 0} color={atsBarColor} />
                <ScoreBar label="Formatting"   value={ats.formatting_score  ?? 0} color={atsBarColor} />
                <ScoreBar label="Experience"   value={ats.experience_score  ?? 0} color={atsBarColor} />
                {(ats.recommendations ?? []).slice(0, 2).map((r: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 rounded-lg border border-brand-100 bg-brand-50/70 px-3.5 py-2.5">
                    <Sparkles size={13} className="text-brand-500 mt-0.5 shrink-0" />
                    <p className="text-xs text-brand-800 leading-relaxed">{r}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3 ring-1 ring-slate-200/70">
                  <FileText size={22} className="text-slate-400" />
                </div>
                <p className="text-sm text-slate-500">No resume uploaded yet</p>
                <Link href="/upload" className="btn-primary mt-4 !py-2 !text-xs !px-4">
                  Upload CV
                </Link>
              </div>
            )}
          </div>

          {/* Career matches */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="subheading">Career Matches</h2>
                <p className="text-xs text-slate-500 mt-0.5">AI-recommended roles</p>
              </div>
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Brain size={17} />
              </span>
            </div>

            {career?.recommended_roles?.length ? (
              <div className="space-y-3.5">
                {(career.recommended_roles as { role: string; confidence_pct: number }[])
                  .slice(0, 5)
                  .map((r, i) => {
                    const barColor =
                      i === 0 ? "bg-brand-600" :
                      i === 1 ? "bg-accent-500" :
                      "bg-slate-300";
                    return (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-xs font-bold tabular-nums text-slate-400 w-4 shrink-0">{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between text-sm mb-1.5">
                            <span className={`font-semibold truncate ${i === 0 ? "text-brand-700" : "text-slate-700"}`}>
                              {r.role}
                            </span>
                            <span className="text-slate-500 ml-2 tabular-nums shrink-0">
                              {r.confidence_pct}%
                            </span>
                          </div>
                          <div className="progress-track">
                            <div className={`progress-fill ${barColor}`} style={{ width: `${r.confidence_pct}%` }} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                <Link
                  href="/dashboard/ai-insights"
                  className="flex items-center justify-end gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 mt-2 transition-colors duration-150"
                >
                  See all 10 roles <ArrowRight size={12} />
                </Link>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3 ring-1 ring-slate-200/70">
                  <Brain size={22} className="text-slate-400" />
                </div>
                <p className="text-sm text-slate-500">Complete your profile to see career matches</p>
              </div>
            )}
          </div>
        </div>

        {/* ── Top job matches ── */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="subheading">Top Job Matches</h2>
              <p className="text-xs text-slate-500 mt-0.5">Ranked by AI match score</p>
            </div>
            <Link href="/jobs" className="flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700 transition-colors duration-150">
              View all <ArrowRight size={14} />
            </Link>
          </div>

          {topJobs.length > 0 ? (
            <div className="space-y-1.5">
              {topJobs.map((job) => {
                const s = job.score ?? 0;
                const skills = job.matched_skills ?? [];
                return (
                  <div
                    key={job.job_id}
                    className="flex items-center gap-4 rounded-lg border border-transparent p-3 transition-all duration-150 hover:border-slate-200 hover:bg-slate-50"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-100 to-brand-50 text-brand-700 font-bold text-sm">
                      {job.company?.[0] ?? "?"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-slate-900 truncate text-sm">{job.title}</p>
                      <p className="text-xs text-slate-500 truncate">{job.company}</p>
                      <div className="flex gap-1 flex-wrap mt-1.5">
                        {skills.slice(0, 3).map((sk: string, i: number) => (
                          <span key={i} className="chip-slate text-2xs">
                            {sk}
                          </span>
                        ))}
                        {skills.length > 3 && (
                          <span className="text-2xs font-medium text-slate-400 self-center">
                            +{skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                    <span className={scoreBadgeClass(s)}>{s}%</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <p className="text-sm text-slate-500">No job matches yet.</p>
              <Link href="/upload" className="btn-outline mt-4 !py-2 !text-xs !px-4">
                Upload CV to get matches
              </Link>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
