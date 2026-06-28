"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { Users, Briefcase, FileCheck2, Tags, FileText, UserCheck, Sparkles, Cpu, RefreshCw } from "lucide-react";
import { admin, humanizeError, type AdminStats, type ModelMetrics, type ModelVersionRow } from "@/lib/api";
import { StatCard, TableShell, Badge } from "@/components/admin/parts";
import ErrorBoundary from "@/components/ErrorBoundary";
import Spinner from "@/components/Spinner";

const ROLE_COLORS = ["#0284c7", "#7c3aed", "#d97706"]; // sky / violet / amber

export default function AdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => { admin.stats().then(setStats).catch((e) => setError(humanizeError(e))); }, []);

  if (error) return <p className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-600">{error}</p>;
  if (!stats) return <div className="flex justify-center py-24"><Spinner size={26} /></div>;

  const roleData = [
    { name: "Candidates", value: stats.users.candidates },
    { name: "Employers",  value: stats.users.employers },
    { name: "Admins",     value: stats.users.admins },
  ];
  const entityData = [
    { name: "Users",  value: stats.users.total },
    { name: "Jobs",   value: stats.jobs.total },
    { name: "Apps",   value: stats.applications },
    { name: "Skills", value: stats.skills },
    { name: "CVs",    value: stats.resumes },
  ];

  return (
    <>
      {/* Hero band */}
      <div className="relative mb-6 overflow-hidden rounded-2xl bg-gradient-aurora bg-grid-light p-6 text-white shadow-green sm:p-7">
        <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div className="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="inline-flex items-center gap-1.5 text-2xs font-semibold uppercase tracking-[0.16em] text-brand-100/80">
              <Sparkles size={12} /> Platform overview
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-[-0.02em] sm:text-3xl">Admin Dashboard</h1>
            <p className="mt-1 max-w-md text-sm text-brand-50/85">
              Manage every user, job, application, skill, and resume across SkillMatch Nepal.
            </p>
          </div>
          <div className="flex gap-6">
            <div><p className="text-3xl font-extrabold tabular-nums">{stats.users.total}</p><p className="text-2xs uppercase tracking-wide text-brand-100/70">Users</p></div>
            <div><p className="text-3xl font-extrabold tabular-nums">{stats.jobs.active}</p><p className="text-2xs uppercase tracking-wide text-brand-100/70">Active jobs</p></div>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Users"        value={stats.users.total}   icon={Users}      accent="sky"    sub={`${stats.users.active} active accounts`}        onClick={() => router.push("/admin/users")} />
        <StatCard label="Jobs"         value={stats.jobs.total}    icon={Briefcase}  accent="violet" sub={`${stats.jobs.active} currently active`}        onClick={() => router.push("/admin/jobs")} />
        <StatCard label="Applications" value={stats.applications}  icon={FileCheck2} accent="amber"  sub="across all postings"                            onClick={() => router.push("/admin/applications")} />
        <StatCard label="Skills"       value={stats.skills}        icon={Tags}       accent="teal"   sub="in matching vocabulary"                         onClick={() => router.push("/admin/skills")} />
        <StatCard label="Resumes"      value={stats.resumes}       icon={FileText}   accent="rose"   sub="uploaded by candidates"                         onClick={() => router.push("/admin/resumes")} />
        <StatCard label="Active users" value={stats.users.active}  icon={UserCheck}  accent="brand"  sub={`${stats.users.total - stats.users.active} inactive`} />
      </div>

      {/* Charts */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Users by role — donut */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-card">
          <h2 className="mb-1 text-sm font-bold text-slate-800">Users by role</h2>
          <p className="mb-4 text-2xs text-slate-500">Distribution across account types</p>
          <ErrorBoundary label="role chart">
            <div className="flex items-center gap-6">
              <ResponsiveContainer width={170} height={170}>
                <PieChart>
                  <Pie data={roleData} dataKey="value" nameKey="name" innerRadius={48} outerRadius={75} paddingAngle={2} stroke="none">
                    {roleData.map((_, i) => <Cell key={i} fill={ROLE_COLORS[i % ROLE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {roleData.map((r, i) => (
                  <div key={r.name} className="flex items-center gap-2 text-sm">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ROLE_COLORS[i] }} />
                    <span className="font-semibold tabular-nums text-slate-800">{r.value}</span>
                    <span className="text-slate-500">{r.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </ErrorBoundary>
        </div>

        {/* Entity totals — bar */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-card">
          <h2 className="mb-1 text-sm font-bold text-slate-800">Platform totals</h2>
          <p className="mb-4 text-2xs text-slate-500">Records by resource type</p>
          <ErrorBoundary label="totals chart">
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={entityData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip cursor={{ fill: "rgba(5,150,105,0.06)" }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} fill="#059669" />
              </BarChart>
            </ResponsiveContainer>
          </ErrorBoundary>
        </div>
      </div>

      <ModelPanel />
    </>
  );
}

function ModelPanel() {
  const [versions, setVersions] = useState<ModelVersionRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [rollingBack, setRollingBack] = useState<number | null>(null);
  const [msg, setMsg] = useState("");

  const load = () => admin.modelVersions().then(setVersions).catch(() => {});
  useEffect(() => { load(); }, []);

  async function retrain() {
    setBusy(true); setMsg("");
    try {
      const m: ModelMetrics = await admin.retrain(800);
      setMsg(`Trained v${m.version ?? "—"} on ${m.n_candidates.toLocaleString()} candidates · accuracy ${(m.accuracy * 100).toFixed(0)}% · AUC ${m.auc.toFixed(2)}`);
      await load();
    } catch (e) {
      setMsg(humanizeError(e));
    } finally {
      setBusy(false);
    }
  }

  async function rollback(version: number) {
    setRollingBack(version); setMsg("");
    try {
      await admin.rollback(version);
      setMsg(`Rolled back to v${version} — it's now the active model.`);
      await load();
    } catch (e) {
      setMsg(humanizeError(e));
    } finally {
      setRollingBack(null);
    }
  }

  return (
    <div className="mt-8">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100"><Cpu size={18} /></span>
          <div>
            <h2 className="text-base font-bold tracking-[-0.01em] text-slate-900">Ranking Model</h2>
            <p className="text-xs text-slate-500">Retrain the RandomForest matcher on the current candidate data</p>
          </div>
        </div>
        <button onClick={retrain} disabled={busy} className="btn-primary !py-2 !px-4 !text-sm">
          {busy
            ? <span className="flex items-center gap-2"><Spinner size={14} /> Training…</span>
            : <><RefreshCw size={14} /> Retrain model</>}
        </button>
      </div>

      {msg && <p className="mb-3 rounded-lg border border-slate-200/70 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-600">{msg}</p>}

      {versions.length > 0 ? (
        <TableShell head={
          <tr>
            <th className="px-4 py-3">Version</th>
            <th className="px-4 py-3">Accuracy</th>
            <th className="px-4 py-3">AUC</th>
            <th className="px-4 py-3">Samples</th>
            <th className="px-4 py-3">Trained</th>
            <th className="px-4 py-3 text-right">Status</th>
          </tr>
        }>
          {versions.map(v => (
            <tr key={v.version} className="transition hover:bg-slate-50/70">
              <td className="px-4 py-3 font-semibold tabular-nums text-slate-800">v{v.version}</td>
              <td className="px-4 py-3 tabular-nums text-slate-600">{(v.accuracy * 100).toFixed(0)}%</td>
              <td className="px-4 py-3 tabular-nums text-slate-600">{v.auc.toFixed(2)}</td>
              <td className="px-4 py-3 tabular-nums text-slate-600">{v.n_samples.toLocaleString()}</td>
              <td className="px-4 py-3 text-xs text-slate-500">{new Date(v.trained_at).toLocaleString()}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end">
                  {v.is_active ? (
                    <Badge tone="green" dot>active</Badge>
                  ) : (
                    <button
                      onClick={() => rollback(v.version)}
                      disabled={rollingBack !== null}
                      className="text-xs font-semibold text-brand-600 hover:text-brand-700 disabled:opacity-50"
                    >
                      {rollingBack === v.version ? "Rolling back…" : "Roll back"}
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </TableShell>
      ) : (
        <div className="rounded-2xl border border-slate-200/80 bg-white p-8 text-center shadow-card">
          <p className="text-sm text-slate-500">No training runs recorded yet — click &ldquo;Retrain model&rdquo; to create the first version.</p>
        </div>
      )}
    </div>
  );
}
