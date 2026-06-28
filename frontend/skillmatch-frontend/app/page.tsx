import React from "react";
import Link from "next/link";
import {
  ArrowRight, Upload, CheckCircle2, Brain, Zap, Target,
  TrendingUp, FileText, ShieldCheck, Building2,
  MapPin, Star, Quote, Sparkles, ChevronRight, Award,
  BookOpen, Rocket, Clock
} from "lucide-react";
import SectionHeading from "@/components/SectionHeading";
import LiveInsights from "@/components/LiveInsights";
import ErrorBoundary from "@/components/ErrorBoundary";
import PublicHomeGate from "@/components/PublicHomeGate";

// ── Score Ring SVG ────────────────────────────────────────────────────────────
function ScoreRing({ pct, size = 100 }: { pct: number; size?: number }) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const fill = (pct / 100) * circ;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label={`${pct} percent match`}>
      <circle cx="50" cy="50" r={r} fill="none" stroke="#d1fae5" strokeWidth="8" />
      <circle
        cx="50" cy="50" r={r} fill="none"
        stroke="#059669" strokeWidth="8"
        strokeDasharray={`${fill} ${circ - fill}`}
        strokeLinecap="round"
        transform="rotate(-90 50 50)"
      />
      <text x="50" y="48" textAnchor="middle" fontSize="17" fontWeight="800" fill="#064e3b">{pct}%</text>
      <text x="50" y="62" textAnchor="middle" fontSize="8"  fontWeight="600" fill="#64748b" letterSpacing="0.08em">MATCH</text>
    </svg>
  );
}

// ── Hero UI mockup ────────────────────────────────────────────────────────────
function HeroMockup() {
  return (
    <div className="relative mx-auto w-full max-w-[400px] lg:ml-auto">
      {/* Ambient glow */}
      <div className="absolute -inset-6 rounded-3xl bg-gradient-to-br from-brand-300/25 to-accent-500/10 blur-3xl" />

      {/* Main card */}
      <div className="relative card shadow-pop p-0 overflow-hidden animate-slide-up">

        {/* Window chrome */}
        <div className="flex items-center gap-1.5 border-b border-slate-100 bg-slate-50/80 px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
          <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
          <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
          <span className="ml-3 inline-flex items-center gap-1.5 rounded-md bg-white px-2 py-0.5 text-2xs font-medium text-slate-400 ring-1 ring-slate-200/80">
            skillmatch.app/dashboard
          </span>
        </div>

        <div className="p-5">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-white">
                <Zap size={11} strokeWidth={2.5} />
              </span>
              <span className="text-xs font-bold text-slate-700">Your top match today</span>
            </div>
            <span className="chip-green gap-1 text-2xs"><Zap size={10} /> New</span>
          </div>

          {/* Job info */}
          <div className="flex items-start gap-4 rounded-xl bg-gradient-to-br from-brand-50 to-brand-100/40 p-4 mb-4">
            {/* Score ring */}
            <div className="shrink-0">
              <ScoreRing pct={92} size={80} />
            </div>
            <div className="min-w-0">
              <p className="font-bold text-slate-900 text-sm leading-snug">Junior ML Engineer</p>
              <p className="text-brand-700 text-xs font-semibold mt-0.5">Fusemachines</p>
              <div className="flex items-center gap-1 text-2xs text-slate-500 mt-1">
                <MapPin size={9} /> Kathmandu
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {["Python", "TensorFlow", "NLP"].map(s => (
                  <span key={s} className="chip text-2xs">{s}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Score bars */}
          <div className="space-y-2.5 mb-4">
            {[
              { label: "Skills matched", val: 83, text: "5 / 6" },
              { label: "Experience fit",  val: 90, text: "Strong" },
              { label: "ATS score",       val: 87, text: "87 / 100" },
            ].map(({ label, val, text }) => (
              <div key={label}>
                <div className="flex justify-between text-2xs mb-1">
                  <span className="text-slate-500">{label}</span>
                  <span className="font-semibold tabular-nums text-slate-800">{text}</span>
                </div>
                <div className="h-1.5 rounded-full bg-brand-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-600"
                    style={{ width: `${val}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <Link href="/register" className="btn-primary w-full justify-center !py-2 !text-xs">
            View full match details <ArrowRight size={12} />
          </Link>
        </div>
      </div>

      {/* Floating notification cards */}
      <div className="absolute -top-4 -right-4 card px-3 py-2 shadow-lift items-center gap-2 animate-float hidden sm:flex">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100">
          <CheckCircle2 size={12} className="text-emerald-600" />
        </span>
        <div>
          <p className="text-2xs font-bold text-slate-800">+3 new matches</p>
          <p className="text-2xs text-slate-500">Just now</p>
        </div>
      </div>

      <div className="absolute -bottom-4 -left-4 card px-3 py-2 shadow-lift items-center gap-2 animate-float-slow hidden sm:flex">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100">
          <Award size={12} className="text-amber-600" />
        </span>
        <div>
          <p className="text-2xs font-bold text-slate-800">ATS Score: 87</p>
          <p className="text-2xs text-slate-500">Top 15% of profiles</p>
        </div>
      </div>

      <div className="absolute top-1/2 -right-6 -translate-y-1/2 card px-3 py-2 shadow-lift hidden xl:flex items-center gap-2">
        <Brain size={13} className="text-brand-600 shrink-0" />
        <p className="text-2xs font-bold text-slate-700 whitespace-nowrap">AI-powered</p>
      </div>
    </div>
  );
}

// ── Testimonials data ─────────────────────────────────────────────────────────
const testimonials = [
  {
    name: "Aarav Sharma",
    role: "Now: ML Engineer at Fusemachines",
    school: "BSc IT · Tribhuvan University",
    text: "SkillMatch Nepal found me a role I would never have found by searching manually. The skill gap tool told me exactly what to learn, and I landed an offer within 3 months.",
    score: 94,
    avatar: "AS",
    color: "from-brand-500 to-brand-700",
  },
  {
    name: "Priya Thapa",
    role: "Now: Data Intern at Khalti",
    school: "BCA · Kathmandu University",
    text: "I uploaded my CV and within minutes I had 12 personalised matches. The ATS feedback helped me rewrite my resume and triple my callback rate.",
    score: 88,
    avatar: "PT",
    color: "from-accent-400 to-accent-700",
  },
  {
    name: "Bibek Karki",
    role: "Now: Frontend Dev at Leapfrog",
    school: "BSc Computing · Softwarica College",
    text: "The best thing about SkillMatch Nepal is that it understands the local IT market. It matched me with companies that actually hire fresh graduates here in Kathmandu.",
    score: 91,
    avatar: "BK",
    color: "from-emerald-400 to-teal-600",
  },
];

// ── Companies data ────────────────────────────────────────────────────────────
// Logos live in /public/logos as static files — swap these SVGs for real
// brand logos any time (keep the same filename) and they update everywhere.
const companies = [
  { name: "Fusemachines",    sector: "AI / ML",        logo: "/logos/fusemachines.svg" },
  { name: "Leapfrog",        sector: "Software",       logo: "/logos/leapfrog.svg" },
  { name: "CloudFactory",    sector: "AI Data",        logo: "/logos/cloudfactory.svg" },
  { name: "Khalti",          sector: "Fintech",        logo: "/logos/khalti.svg" },
  { name: "F1Soft",          sector: "Fintech",        logo: "/logos/f1soft.svg" },
  { name: "Cotiviti Nepal",  sector: "Healthcare IT",  logo: "/logos/cotiviti.svg" },
  { name: "Verisk Nepal",    sector: "Analytics",      logo: "/logos/verisk.svg" },
  { name: "Deerwalk",        sector: "Healthcare IT",  logo: "/logos/deerwalk.svg" },
];

// ── Feature icons ─────────────────────────────────────────────────────────────
const featureIcons: Record<string, React.ReactNode> = {
  BrainCircuit: <Brain size={21} />,
  FileSearch:   <FileText size={21} />,
  MapPin:       <MapPin size={21} />,
  Target:       <Target size={21} />,
  ShieldCheck:  <ShieldCheck size={21} />,
  Building2:    <Building2 size={21} />,
  TrendingUp:   <TrendingUp size={21} />,
  BookOpen:     <BookOpen size={21} />,
  Rocket:       <Rocket size={21} />,
};

const featureBg = [
  "bg-brand-50 text-brand-600",
  "bg-accent-50 text-accent-600",
  "bg-amber-50 text-amber-600",
  "bg-sky-50 text-sky-600",
  "bg-violet-50 text-violet-600",
  "bg-emerald-50 text-emerald-600",
];

// ── Steps ─────────────────────────────────────────────────────────────────────
const stepIcons = [Upload, Brain, Rocket];

// ── Page ──────────────────────────────────────────────────────────────────────
import { features, steps, stats } from "@/lib/data";

export default function HomePage() {
  return (
    <PublicHomeGate>
      {/* ════════════════════════════════════ HERO ════════════════════════ */}
      <section className="relative overflow-hidden bg-gradient-hero bg-grid">
        {/* Decorative blobs */}
        <div className="pointer-events-none absolute -top-52 -right-52 h-[700px] w-[700px] rounded-full bg-brand-400/10 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-[400px] w-[400px] rounded-full bg-accent-600/5 blur-3xl" />

        <div className="container-px relative grid items-center gap-16 py-20 lg:grid-cols-2 lg:py-28 xl:py-32">
          {/* Copy */}
          <div className="space-y-7 animate-slide-up">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand-200/80 bg-white px-4 py-1.5 shadow-sm">
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand-600">
                <Sparkles size={9} className="text-white" />
              </span>
              <span className="text-xs font-semibold text-brand-700">
                Nepal&apos;s first ML-powered job matching platform
              </span>
            </div>

            <h1 className="display">
              Your skills deserve{" "}
              <span className="relative inline-block">
                <span className="text-gradient">the right job.</span>
                <svg className="absolute -bottom-2 left-0 w-full" height="6" viewBox="0 0 300 6" fill="none" aria-hidden="true">
                  <path d="M0 5 Q75 0 150 4 Q225 8 300 3" stroke="#059669" strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.55"/>
                </svg>
              </span>
            </h1>

            <p className="body-lg max-w-[520px]">
              SkillMatch Nepal uses machine learning to understand your resume, extract
              your real skills, and match you with IT roles in Kathmandu that actually fit —
              not just roles with matching keywords.
            </p>

            <div className="flex flex-col gap-3 sm:flex-row">
              <Link href="/upload" className="btn-primary !py-3.5 !px-7 !text-md group">
                <Upload size={17} strokeWidth={2.5} />
                Upload your resume
                <ChevronRight size={15} className="opacity-60 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link href="/jobs" className="btn-outline !py-3.5 !px-7 !text-md">
                Browse all jobs
                <ArrowRight size={16} />
              </Link>
            </div>

            {/* Trust strip */}
            <div className="flex flex-wrap gap-x-6 gap-y-2.5 pt-1">
              {[
                "Free for all graduates",
                "Skills-based, not keyword-based",
                "Nepal-first",
              ].map((label) => (
                <span key={label} className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600">
                  <CheckCircle2 size={14} className="text-brand-600" />{label}
                </span>
              ))}
            </div>
          </div>

          {/* Mockup */}
          <HeroMockup />
        </div>
      </section>

      {/* ══════════════════════════════ TRUST LOGOS ═══════════════════════ */}
      <section className="border-y border-slate-200/70 bg-white py-8">
        <div className="container-px">
          <p className="text-center text-xs font-semibold uppercase tracking-[0.15em] text-slate-400 mb-6">
            Matching graduates to Nepal&apos;s top IT employers
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {companies.slice(0, 6).map(c => (
              <div key={c.name} className="flex items-center gap-2 text-slate-500 hover:text-brand-600 transition-colors duration-150">
                <img src={c.logo} alt={`${c.name} logo`} width={22} height={22} loading="lazy" className="h-[22px] w-[22px] rounded-md" />
                <span className="text-sm font-semibold tracking-[-0.01em]">{c.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════ STATS BAR ═════════════════════════ */}
      <section className="bg-gradient-brand py-12">
        <div className="container-px grid grid-cols-2 gap-6 lg:grid-cols-4">
          {stats.map((s, i) => {
            const icons = [TrendingUp, Star, Zap, Building2];
            const Icon = icons[i] ?? Star;
            return (
              <div key={s.label} className="flex flex-col items-center text-center">
                <span className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-white/15 text-white/90">
                  <Icon size={17} />
                </span>
                <p className="text-2xl font-bold tabular-nums tracking-[-0.02em] text-white sm:text-3xl">{s.value}</p>
                <p className="mt-1 text-xs text-brand-100/90 leading-snug max-w-[120px]">{s.label}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ═══════════════════════════ LIVE INSIGHTS ════════════════════════ */}
      <section className="section-alt">
        <div className="container-px">
          <SectionHeading
            center
            eyebrow="Live insights"
            title="A platform that moves in real time"
            subtitle="Matching scores, applications, skill demand, and hiring — visualised. Hover to pause, or tap a metric to explore."
          />
          <div className="mt-12">
            <ErrorBoundary label="insights">
              <LiveInsights />
            </ErrorBoundary>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════ FEATURES ══════════════════════════ */}
      <section className="section container-px">
        <SectionHeading
          center
          eyebrow="Why SkillMatch Nepal"
          title="Smarter matching, built for Nepal"
          subtitle="We combine semantic NLP with a local-first approach so graduates and employers connect on what really matters: actual skills."
        />

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div
              key={f.title}
              className="group card-hover p-6"
            >
              <span className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-105 ${featureBg[i % featureBg.length]}`}>
                {featureIcons[f.icon] ?? <Zap size={21} />}
              </span>
              <h3 className="text-md font-semibold tracking-[-0.01em] text-slate-900 mb-2">{f.title}</h3>
              <p className="text-sm leading-relaxed text-slate-500">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════ HOW IT WORKS ═════════════════════════ */}
      <section className="section-alt">
        <div className="container-px">
          <SectionHeading
            center
            eyebrow="How it works"
            title="Three steps to your next role"
            subtitle="From raw resume to ranked job matches in under 60 seconds."
          />

          <div className="relative mt-14 grid gap-6 md:grid-cols-3">
            {/* Connecting dashed line */}
            <div className="absolute top-12 left-[calc(16.66%+2rem)] right-[calc(16.66%+2rem)] hidden h-px border-t-2 border-dashed border-brand-200 md:block" />

            {steps.map((s, i) => {
              const Icon = stepIcons[i];
              return (
                <div key={s.step} className="relative card p-7 flex flex-col items-center text-center group hover:shadow-lift hover:border-slate-300 transition-all duration-200">
                  <div className="relative mb-5">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-brand shadow-green group-hover:scale-105 transition-transform duration-200">
                      <Icon size={22} className="text-white" strokeWidth={2} />
                    </div>
                    <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-sm border border-brand-100 text-2xs font-bold tabular-nums text-brand-600">
                      {s.step}
                    </span>
                  </div>
                  <h3 className="text-md font-bold tracking-[-0.01em] text-slate-900 mb-2">{s.title}</h3>
                  <p className="text-sm text-slate-500 leading-relaxed">{s.description}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-10 flex justify-center">
            <Link href="/upload" className="btn-primary !py-3.5 !px-8 !text-md">
              <Rocket size={16} /> Start matching now — it&apos;s free
            </Link>
          </div>
        </div>
      </section>

      {/* ════════════════════════════ TESTIMONIALS ════════════════════════ */}
      <section className="section container-px">
        <SectionHeading
          center
          eyebrow="Success stories"
          title="Graduates who found their fit"
          subtitle="Real students from Kathmandu who used SkillMatch Nepal to land their first IT roles."
        />

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="card-hover p-6 flex flex-col gap-5"
            >
              {/* Quote */}
              <div className="flex items-start gap-3">
                <Quote size={20} className="text-brand-300 shrink-0 mt-0.5" />
                <p className="text-sm leading-relaxed text-slate-600">{t.text}</p>
              </div>

              {/* Stars */}
              <div className="flex gap-0.5" role="img" aria-label="5 out of 5 stars">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={13} className="fill-amber-400 text-amber-400" />
                ))}
              </div>

              {/* Author */}
              <div className="flex items-center gap-3 pt-2 border-t border-slate-100">
                <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${t.color} text-white text-sm font-bold`}>
                  {t.avatar}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-slate-900 text-sm">{t.name}</p>
                  <p className="text-2xs text-brand-600 font-medium truncate">{t.role}</p>
                  <p className="text-2xs text-slate-500 truncate">{t.school}</p>
                </div>
                <span className="ml-auto shrink-0 chip-green text-2xs">{t.score}% match</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════ COMPANIES HIRING ═════════════════════════ */}
      <section className="section-alt">
        <div className="container-px">
          <SectionHeading
            center
            eyebrow="Companies hiring"
            title="Nepal's top IT employers in one place"
          />

          <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {companies.map((c) => (
              <div
                key={c.name}
                className="card-hover flex flex-col items-center justify-center p-5 text-center group"
              >
                <div className="mb-3 h-12 w-12 overflow-hidden rounded-xl ring-1 ring-slate-200/70 transition-all duration-200 group-hover:ring-brand-200">
                  <img
                    src={c.logo}
                    alt={`${c.name} logo`}
                    width={48}
                    height={48}
                    loading="lazy"
                    className="h-full w-full object-cover"
                  />
                </div>
                <p className="font-semibold text-slate-800 text-sm tracking-[-0.01em]">{c.name}</p>
                <p className="text-2xs text-slate-500 mt-0.5">{c.sector}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex justify-center">
            <Link href="/jobs" className="btn-outline !px-7 !py-3 !text-md">
              Browse all open roles <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════ FINAL CTA ═════════════════════════ */}
      <section className="container-px pb-24 pt-8">
        <div className="relative overflow-hidden rounded-2xl shadow-green">
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-aurora" />
          <div className="absolute inset-0 bg-dots opacity-20" />
          <div className="absolute -top-16 -right-16 h-56 w-56 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute -bottom-16 -left-16 h-56 w-56 rounded-full bg-white/10 blur-3xl" />

          <div className="relative px-8 py-16 text-center sm:px-16">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1.5">
              <Star size={12} className="text-amber-300 fill-amber-300" />
              <span className="text-xs font-bold text-white/90">Free for every IT graduate in Nepal</span>
            </div>

            <h2 className="text-3xl font-bold tracking-[-0.02em] text-white sm:text-4xl lg:text-5xl leading-tight">
              Ready to find the job<br className="hidden sm:block" /> you actually deserve?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-brand-100/90 text-md leading-relaxed">
              Upload your resume and get AI-powered matches in under 60 seconds.
              No account needed to browse — sign up only when you find a role you love.
            </p>

            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/upload" className="btn-white !py-3.5 !px-8 !text-md group">
                <Upload size={17} />
                Upload resume — free
                <ChevronRight size={14} className="opacity-50 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link href="/register" className="btn !py-3.5 !px-8 !text-md border border-white/25 text-white hover:bg-white/10 transition">
                Create account
              </Link>
            </div>

            {/* Footer trust row */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
              {[
                { icon: <Clock size={12} />,        text: "Results in 60 seconds" },
                { icon: <ShieldCheck size={12} />,  text: "Your data stays private" },
                { icon: <Award size={12} />,         text: "No hidden fees ever" },
              ].map(({ icon, text }) => (
                <span key={text} className="flex items-center gap-1.5 text-xs text-white/70">
                  {icon}{text}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>
    </PublicHomeGate>
  );
}
