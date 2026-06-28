"use client";

/**
 * AI Insights Dashboard
 * Endpoint: GET /api/matching/dashboard/
 *
 * Sections:
 *   1. Profile Summary card
 *   2. ATS Score — radial gauge + 5 dimension bars
 *   3. Career Recommendations — horizontal confidence bars (top 10)
 *   4. Skill Gap — for the top matched job
 *   5. Top Job Matches — score cards
 *   6. Learning Path — priority list
 */

import { useEffect, useState } from "react";
import {
  RadialBarChart, RadialBar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from "recharts";
import {
  BrainCircuit, User, GraduationCap, Building2, BarChart3, Wrench,
  ClipboardList, FileText, Target, CheckCircle2, AlertTriangle,
  Lightbulb, Briefcase, BookOpen, ArrowRight, Sparkles,
} from "lucide-react";
import { matching, tokens, humanizeError } from "@/lib/api";
import { scoreHex as scoreColor, scoreLabel } from "@/lib/score";

// ── Types ────────────────────────────────────────────────────────────────────
interface ProfileData {
  full_name: string;
  email: string;
  degree: string;
  university: string;
  cgpa: number | null;
  skills_count: number;
  ats_score: number;
  resume_score: number;
  hiring_probability: number;
  preferred_role: string;
}

interface ATSData {
  ats_score: number;
  completeness_score: number;
  keyword_score: number;
  formatting_score: number;
  experience_score: number;
  social_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

interface CareerRole {
  role: string;
  confidence: number;
  confidence_pct: number;
  reason: string;
  missing_skills: string[];
}

interface LearningPath {
  skill: string;
  priority: "high" | "medium" | "low";
  resources: string[];
  reason: string;
}

interface JobMatch {
  job_id: number;
  title: string;
  company: string;
  score: number;
  similarity: number;
  matched_skills: string[];
}

interface DashboardData {
  profile: ProfileData;
  ats_analysis: ATSData;
  career_recommendations: {
    recommended_roles: CareerRole[];
    learning_paths: LearningPath[];
    top_role: string;
  };
  top_job_matches: JobMatch[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────
async function fetchDashboard(): Promise<DashboardData> {
  // Use the shared API client so auth headers, token refresh, timeout and the
  // structured error envelope are all handled consistently.
  return matching.dashboard() as unknown as Promise<DashboardData>;
}

function getToken(): string {
  if (typeof window === "undefined") return "";
  // Tokens are stored under the "sm_access" key by the auth/token helpers.
  return tokens.getAccess() || "";
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const data = [{ name: label, value: score, fill: scoreColor(score) }];
  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width={160} height={160}>
        <RadialBarChart
          cx="50%" cy="50%"
          innerRadius="60%" outerRadius="90%"
          startAngle={210} endAngle={-30}
          data={data}
        >
          <RadialBar
            background={{ fill: "#e2e8f0" }}
            dataKey="value"
            cornerRadius={8}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      <span className="text-4xl font-bold tabular-nums tracking-[-0.02em] -mt-12" style={{ color: scoreColor(score) }}>
        {score}
      </span>
      <span className="text-sm text-slate-500 mt-1">{scoreLabel(score)}</span>
      <span className="text-2xs font-semibold text-slate-400 uppercase tracking-[0.08em]">{label}</span>
    </div>
  );
}

function DimBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-32 text-right text-slate-600 shrink-0">{label}</span>
      <div className="flex-1 progress-track !h-2.5">
        <div
          className="progress-fill"
          style={{ width: `${value}%`, backgroundColor: scoreColor(value) }}
        />
      </div>
      <span className="w-8 text-right font-semibold tabular-nums text-slate-700">{value}</span>
    </div>
  );
}

function JobCard({ match }: { match: JobMatch }) {
  return (
    <div className="card-hover p-4">
      <div className="flex justify-between items-start mb-2">
        <div className="min-w-0">
          <h4 className="font-semibold text-slate-900 text-sm truncate">{match.title}</h4>
          <p className="text-xs text-slate-500 truncate">{match.company}</p>
        </div>
        <span
          className="text-xl font-bold tabular-nums shrink-0 ml-2"
          style={{ color: scoreColor(match.score) }}
        >
          {match.score}
          <span className="text-xs text-slate-500 font-normal">/100</span>
        </span>
      </div>
      <div className="progress-track mb-3">
        <div
          className="progress-fill"
          style={{ width: `${match.score}%`, backgroundColor: scoreColor(match.score) }}
        />
      </div>
      {match.matched_skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {match.matched_skills.slice(0, 5).map((s) => (
            <span key={s} className="chip text-2xs">
              {s}
            </span>
          ))}
          {match.matched_skills.length > 5 && (
            <span className="text-xs font-medium text-slate-500 self-center">+{match.matched_skills.length - 5}</span>
          )}
        </div>
      )}
    </div>
  );
}

function SectionTitle({ icon: Icon, children }: { icon: React.ElementType; children: React.ReactNode }) {
  return (
    <h2 className="flex items-center gap-2.5 text-lg font-bold tracking-[-0.01em] text-slate-900">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
        <Icon size={16} />
      </span>
      {children}
    </h2>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AIDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setError("Please log in to view your AI insights.");
      setLoading(false);
      return;
    }
    fetchDashboard()
      .then(setData)
      .catch((e) => setError(humanizeError(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" role="status" aria-label="Loading" />
          <p className="text-slate-600">Analysing your profile with AI…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc] px-4">
        <div className="card border-red-200/70 bg-red-50/60 p-6 max-w-md text-center">
          <AlertTriangle size={22} className="mx-auto mb-2 text-red-500" />
          <p className="text-red-700 font-medium">{error || "Could not load dashboard."}</p>
          <p className="text-sm text-red-500/90 mt-2">
            Make sure you are logged in and have uploaded a resume.
          </p>
        </div>
      </div>
    );
  }

  const { profile, ats_analysis: ats, career_recommendations: career, top_job_matches } = data;
  const hiringPct = Math.round((profile.hiring_probability || 0) * 100);

  // Career bar chart data
  const careerChartData = (career.recommended_roles || []).slice(0, 10).map((r) => ({
    role: r.role.replace(" Developer", " Dev").replace(" Engineer", " Eng"),
    pct: r.confidence_pct,
    fill: scoreColor(r.confidence_pct),
  }));

  // ATS dimension chart
  const atsDimensions = [
    { label: "Completeness", value: ats.completeness_score ?? 0 },
    { label: "Keywords",     value: ats.keyword_score      ?? 0 },
    { label: "Formatting",   value: ats.formatting_score   ?? 0 },
    { label: "Experience",   value: ats.experience_score   ?? 0 },
    { label: "Social",       value: ats.social_score       ?? 0 },
  ];

  const profileChips = [
    { icon: User,          text: profile.full_name },
    { icon: GraduationCap, text: profile.degree || "—" },
    { icon: Building2,     text: profile.university || "—" },
    ...(profile.cgpa ? [{ icon: BarChart3, text: `CGPA ${profile.cgpa}` }] : []),
    { icon: Wrench,        text: `${profile.skills_count} skills` },
  ];

  const scoreCards = [
    { label: "ATS Score",        value: profile.ats_score,    icon: ClipboardList },
    { label: "Resume Score",     value: profile.resume_score, icon: FileText },
    { label: "Top Role Fit",     value: career.recommended_roles?.[0]?.confidence_pct ?? 0, icon: Target },
    { label: "Hire Probability", value: hiringPct,            icon: CheckCircle2 },
  ];

  return (
    <main className="min-h-screen bg-[#f8fafc] p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* ── Header ── */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-aurora p-6 sm:p-7 text-white shadow-green">
          <div className="absolute inset-0 bg-grid opacity-15" />
          <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
          <div className="relative">
            <h1 className="flex items-center gap-2.5 text-2xl font-bold tracking-[-0.02em] mb-1">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
                <BrainCircuit size={19} />
              </span>
              AI Insights Dashboard
            </h1>
            <p className="text-brand-100/75 text-sm">Powered by Sentence-BERT · XGBoost · spaCy · SkillMatch Nepal</p>
            <div className="mt-4 flex flex-wrap gap-2.5 text-sm">
              {profileChips.map(({ icon: Icon, text }, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 rounded-lg border border-white/15 bg-white/10 px-3 py-1 backdrop-blur-sm">
                  <Icon size={13} className="text-brand-200" />
                  {text}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Score cards row ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {scoreCards.map(({ label, value, icon: Icon }) => (
            <div key={label} className="card p-4 text-center transition-all duration-200 hover:border-slate-300 hover:shadow-lift">
              <span className="mx-auto mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-50 text-slate-500 ring-1 ring-slate-200/70">
                <Icon size={16} />
              </span>
              <div className="text-3xl font-bold tabular-nums tracking-[-0.02em]" style={{ color: scoreColor(value) }}>{value}</div>
              <div className="text-xs text-slate-500 mt-1">{label}</div>
              <div className="progress-track mt-2.5">
                <div className="progress-fill" style={{ width: `${value}%`, backgroundColor: scoreColor(value) }} />
              </div>
            </div>
          ))}
        </div>

        {/* ── ATS Analysis ── */}
        {ats.ats_score != null && (
          <div className="card p-6">
            <div className="mb-5">
              <SectionTitle icon={ClipboardList}>ATS Compatibility Analysis</SectionTitle>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {/* Gauge */}
              <div className="flex flex-col items-center justify-center">
                <ScoreGauge score={ats.ats_score} label="ATS Score" />
              </div>
              {/* Dimension bars */}
              <div className="md:col-span-2 space-y-3 self-center">
                {atsDimensions.map((d) => (
                  <DimBar key={d.label} label={d.label} value={d.value} />
                ))}
              </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid md:grid-cols-2 gap-4 mt-6">
              {ats.strengths?.length > 0 && (
                <div className="rounded-lg border border-emerald-200/60 bg-emerald-50/50 p-4">
                  <h3 className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 mb-2">
                    <CheckCircle2 size={14} /> Strengths
                  </h3>
                  <ul className="space-y-1.5">
                    {ats.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-slate-700 flex gap-2">
                        <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" /> {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {ats.weaknesses?.length > 0 && (
                <div className="rounded-lg border border-red-200/60 bg-red-50/50 p-4">
                  <h3 className="flex items-center gap-1.5 text-sm font-semibold text-red-600 mb-2">
                    <AlertTriangle size={14} /> Areas to Improve
                  </h3>
                  <ul className="space-y-1.5">
                    {ats.weaknesses.map((w, i) => (
                      <li key={i} className="text-sm text-slate-700 flex gap-2">
                        <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" /> {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {ats.recommendations?.length > 0 && (
              <div className="mt-4 rounded-lg border border-amber-200/70 bg-amber-50/70 p-4">
                <h3 className="flex items-center gap-1.5 text-sm font-semibold text-amber-700 mb-2">
                  <Lightbulb size={14} /> Recommendations
                </h3>
                <ol className="space-y-1.5 list-decimal list-inside">
                  {ats.recommendations.map((r, i) => (
                    <li key={i} className="text-sm text-amber-900/90">{r}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        {/* ── Career Recommendations ── */}
        {career.recommended_roles?.length > 0 && (
          <div className="card p-6">
            <SectionTitle icon={Target}>Career Recommendations</SectionTitle>
            <p className="text-sm text-slate-500 mt-1.5 mb-4">
              Top role: <strong className="text-brand-700">{career.top_role}</strong>
            </p>
            <ResponsiveContainer width="100%" height={340}>
              <BarChart
                data={careerChartData}
                layout="vertical"
                margin={{ top: 0, right: 50, left: 140, bottom: 0 }}
              >
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} stroke="#e2e8f0" />
                <YAxis type="category" dataKey="role" tick={{ fontSize: 11, fill: "#334155" }} width={140} stroke="#e2e8f0" />
                <Tooltip
                  formatter={(val: number) => [`${val}%`, "Confidence"]}
                  cursor={{ fill: "#f1f5f9" }}
                  contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12, boxShadow: "0 4px 12px -2px rgba(15,23,42,0.08)" }}
                />
                <Bar dataKey="pct" radius={[0, 6, 6, 0]}>
                  {careerChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Role detail cards */}
            <div className="mt-4 grid sm:grid-cols-2 gap-3">
              {career.recommended_roles.slice(0, 4).map((r, i) => (
                <div key={i} className="rounded-lg border border-slate-200/80 bg-slate-50/70 p-3.5">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-sm text-slate-800">{r.role}</span>
                    <span className="font-bold text-sm tabular-nums" style={{ color: scoreColor(r.confidence_pct) }}>
                      {r.confidence_pct}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{r.reason}</p>
                  {r.missing_skills.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {r.missing_skills.map((s) => (
                        <span key={s} className="chip-red text-2xs">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Top Job Matches ── */}
        {top_job_matches?.length > 0 && (
          <div className="card p-6">
            <div className="mb-4">
              <SectionTitle icon={Briefcase}>Top Job Matches</SectionTitle>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {top_job_matches.map((match) => (
                <JobCard key={match.job_id} match={match} />
              ))}
            </div>
          </div>
        )}

        {/* ── Learning Path ── */}
        {career.learning_paths?.length > 0 && (
          <div className="card p-6">
            <div className="mb-4">
              <SectionTitle icon={BookOpen}>Learning Roadmap</SectionTitle>
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              {career.learning_paths.map((lp, i) => (
                <div
                  key={i}
                  className={`rounded-lg p-4 border ${
                    lp.priority === "high"
                      ? "bg-red-50/60 border-red-200/70"
                      : "bg-amber-50/60 border-amber-200/70"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-semibold text-slate-800 text-sm">{lp.skill}</span>
                    <span
                      className={`text-2xs px-2 py-0.5 rounded-md font-bold uppercase tracking-[0.06em] ${
                        lp.priority === "high"
                          ? "bg-red-100 text-red-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {lp.priority}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2.5 leading-relaxed">{lp.reason}</p>
                  <ul className="space-y-1.5">
                    {lp.resources.map((r, j) => (
                      <li key={j} className="text-xs font-medium text-brand-700 flex gap-1.5 items-start">
                        <ArrowRight size={11} className="mt-0.5 shrink-0" /> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <p className="flex items-center justify-center gap-1.5 text-center text-xs text-slate-500 pb-4">
          <Sparkles size={11} className="text-brand-400" />
          SkillMatch Nepal · AI Resume Intelligence Platform · Results update on each resume upload
        </p>
      </div>
    </main>
  );
}
