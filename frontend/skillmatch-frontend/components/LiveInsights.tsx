"use client";

import { useEffect, useRef, useState } from "react";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

/* ──────────────────────────────────────────────────────────────────────────
   Live Insights — a premium, self-animating analytics card for the homepage.
   Cycles through several fake datasets, smoothly morphing the chart and the
   KPI counters between them. Pure SVG + requestAnimationFrame (no deps).
   Visual only — no real data, no business logic.
─────────────────────────────────────────────────────────────────────────── */

type Fmt = "pct" | "k" | "int" | "h";
interface Kpi { label: string; value: number; fmt: Fmt; delta: string; good?: boolean }
interface Scenario { id: string; label: string; color: string; series: number[]; kpis: Kpi[] }

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const SCENARIOS: Scenario[] = [
  {
    id: "matches", label: "Job matches", color: "#059669",
    series: [42, 48, 45, 58, 63, 60, 72, 78, 74, 86, 90, 94],
    kpis: [
      { label: "Avg match score", value: 87, fmt: "pct", delta: "+6%" },
      { label: "Weekly matches", value: 1240, fmt: "k", delta: "+14%" },
      { label: "Active seekers", value: 3820, fmt: "k", delta: "+9%" },
    ],
  },
  {
    id: "apps", label: "Applications", color: "#0d9488",
    series: [30, 34, 40, 38, 46, 52, 50, 58, 64, 62, 70, 76],
    kpis: [
      { label: "Applications", value: 3400, fmt: "k", delta: "+11%" },
      { label: "Response rate", value: 62, fmt: "pct", delta: "+4%" },
      { label: "Avg reply time", value: 18, fmt: "h", delta: "-12%", good: true },
    ],
  },
  {
    id: "skills", label: "Skill demand", color: "#0284c7",
    series: [55, 52, 60, 58, 66, 70, 68, 75, 72, 80, 84, 88],
    kpis: [
      { label: "Skills tracked", value: 38, fmt: "int", delta: "+3" },
      { label: "Top: React", value: 91, fmt: "pct", delta: "+7%" },
      { label: "Roles covered", value: 10, fmt: "int", delta: "+2" },
    ],
  },
  {
    id: "hires", label: "Hiring funnel", color: "#d97706",
    series: [20, 26, 24, 32, 38, 36, 44, 48, 52, 58, 62, 68],
    kpis: [
      { label: "Shortlisted", value: 540, fmt: "int", delta: "+18%" },
      { label: "Interviews", value: 210, fmt: "int", delta: "+10%" },
      { label: "Offers", value: 64, fmt: "int", delta: "+15%" },
    ],
  },
];

const W = 640, H = 240, PADX = 18, PADT = 16, PADB = 26;
const xAt = (i: number, n: number) => PADX + (i * (W - 2 * PADX)) / (n - 1);
const yAt = (v: number) => PADT + (1 - v / 100) * (H - PADT - PADB);

function smoothPath(pts: { x: number; y: number }[]): string {
  if (pts.length < 2) return "";
  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const c1x = p1.x + (p2.x - p0.x) / 6, c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6, c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }
  return d;
}

function fmtValue(v: number, fmt: Fmt): string {
  switch (fmt) {
    case "pct": return `${Math.round(v)}%`;
    case "h":   return `${Math.round(v)}h`;
    case "k":   return v >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${Math.round(v)}`;
    default:    return `${Math.round(v)}`;
  }
}

export default function LiveInsights() {
  const [idx, setIdx] = useState(0);
  const [disp, setDisp] = useState<number[]>(SCENARIOS[0].series);
  const [kpi, setKpi] = useState<number[]>(SCENARIOS[0].kpis.map((k) => k.value));
  const [paused, setPaused] = useState(false);
  const fromRef = useRef({ series: SCENARIOS[0].series, kpis: SCENARIOS[0].kpis.map((k) => k.value) });
  const rafRef = useRef(0);

  // Smoothly morph from the current values to the selected scenario.
  useEffect(() => {
    const target = SCENARIOS[idx];
    const from = fromRef.current;
    const start = performance.now();
    const dur = 900;
    cancelAnimationFrame(rafRef.current);
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / dur);
      const e = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setDisp(target.series.map((v, i) => from.series[i] + (v - from.series[i]) * e));
      setKpi(target.kpis.map((k, i) => from.kpis[i] + (k.value - from.kpis[i]) * e));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
      else fromRef.current = { series: target.series, kpis: target.kpis.map((k) => k.value) };
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [idx]);

  // Auto-advance through scenarios unless the user is hovering.
  useEffect(() => {
    if (paused) return;
    const id = setInterval(() => setIdx((i) => (i + 1) % SCENARIOS.length), 4500);
    return () => clearInterval(id);
  }, [paused]);

  const active = SCENARIOS[idx];
  const n = disp.length;
  const pts = disp.map((v, i) => ({ x: xAt(i, n), y: yAt(v) }));
  const line = smoothPath(pts);
  const area = `${line} L ${xAt(n - 1, n).toFixed(1)} ${H - PADB} L ${xAt(0, n).toFixed(1)} ${H - PADB} Z`;
  const last = pts[pts.length - 1];

  return (
    <div
      className="mx-auto max-w-4xl overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-pop"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Header */}
      <div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-7">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
            <Activity size={17} />
          </span>
          <div>
            <p className="text-sm font-bold text-slate-800">Platform insights</p>
            <p className="text-2xs text-slate-500">Live demo · auto-updating</p>
          </div>
        </div>
        {/* Scenario tabs */}
        <div className="flex flex-wrap gap-1.5">
          {SCENARIOS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setIdx(i)}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                i === idx ? "text-white shadow-sm" : "text-slate-500 hover:bg-slate-100"
              }`}
              style={i === idx ? { backgroundColor: s.color } : undefined}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="px-3 pt-5 sm:px-5" style={{ color: active.color, transition: "color 700ms ease" }}>
        <svg viewBox={`0 0 ${W} ${H}`} className="h-56 w-full sm:h-64" role="img" aria-label={`${active.label} trend`}>
          <defs>
            <linearGradient id="liveFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* gridlines */}
          {[0, 25, 50, 75, 100].map((g) => (
            <line key={g} x1={PADX} x2={W - PADX} y1={yAt(g)} y2={yAt(g)}
              stroke="#e2e8f0" strokeWidth="1" strokeDasharray={g === 0 ? "0" : "3 5"} />
          ))}

          {/* area + line */}
          <path d={area} fill="url(#liveFill)" />
          <path d={line} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

          {/* leading marker */}
          <line x1={last.x} y1={PADT} x2={last.x} y2={H - PADB} stroke="currentColor" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="3 4" />
          <circle cx={last.x} cy={last.y} r="6" fill="currentColor" opacity="0.18" />
          <circle cx={last.x} cy={last.y} r="3.5" fill="#fff" stroke="currentColor" strokeWidth="2.5" />

          {/* x labels */}
          {MONTHS.map((m, i) => (i % 2 === 0 ? (
            <text key={m} x={xAt(i, n)} y={H - 8} textAnchor="middle" fontSize="10" fill="#94a3b8" fontWeight="600">{m}</text>
          ) : null))}
        </svg>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-3 gap-px border-t border-slate-100 bg-slate-100">
        {active.kpis.map((k, i) => {
          const up = !k.delta.startsWith("-");
          const good = k.good ?? up;
          return (
            <div key={k.label} className="bg-white px-4 py-4 text-center sm:px-5">
              <p className="text-xl font-extrabold tracking-tight text-slate-900 tabular-nums sm:text-2xl">
                {fmtValue(kpi[i], k.fmt)}
              </p>
              <p className="mt-0.5 truncate text-2xs text-slate-500">{k.label}</p>
              <span className={`mt-1.5 inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-2xs font-semibold ${
                good ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"
              }`}>
                {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                {k.delta}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
