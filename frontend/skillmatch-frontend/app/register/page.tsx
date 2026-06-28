"use client";

import { useState, useEffect, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Eye, EyeOff, User, Briefcase, AlertTriangle,
  FileText, Target, BarChart3, Rocket,
  Search, Zap, ClipboardList, Mail, Lock,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { APIError, humanizeError, homeForRole } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import Logo from "@/components/Logo";
import Spinner from "@/components/Spinner";

type Role = "candidate" | "employer";

// Visual-only password strength (does not change validation).
function scorePassword(pw: string): number {
  if (!pw) return 0;
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(4, s);
}
const STRENGTH = [
  { label: "", color: "" },
  { label: "Weak", color: "bg-red-500" },
  { label: "Fair", color: "bg-amber-500" },
  { label: "Good", color: "bg-brand-500" },
  { label: "Strong", color: "bg-emerald-600" },
] as const;

function PasswordMeter({ value }: { value: string }) {
  if (!value) return null;
  const score = scorePassword(value);
  const meta = STRENGTH[score] || STRENGTH[1];
  return (
    <div className="mt-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <span key={i} className={`h-1.5 flex-1 rounded-full transition-colors duration-200 ${i <= score ? meta.color : "bg-slate-200"}`} />
        ))}
      </div>
      <p className="mt-1 text-2xs font-medium text-slate-500">
        Password strength: <span className="font-semibold text-slate-700">{meta.label || "—"}</span>
      </p>
    </div>
  );
}

const roleBenefits = {
  candidate: [
    { icon: FileText,      label: "CV Analysis" },
    { icon: Target,        label: "Job Matching" },
    { icon: BarChart3,     label: "ATS Scoring" },
    { icon: Rocket,        label: "Career Paths" },
  ],
  employer: [
    { icon: Search,        label: "Smart Search" },
    { icon: Zap,           label: "Instant Rank" },
    { icon: ClipboardList, label: "Skill Match" },
    { icon: Mail,          label: "Auto Alerts" },
  ],
} as const;

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [role,      setRole]     = useState<Role>("candidate");
  const [fullName,  setFullName]  = useState("");

  // Honor ?role=employer (e.g. from "Employer Signup" links) and preselect
  // the matching tab. Read from the URL directly to avoid a Suspense
  // boundary requirement around useSearchParams.
  useEffect(() => {
    const r = new URLSearchParams(window.location.search).get("role");
    if (r === "employer" || r === "candidate") setRole(r);
  }, []);
  const [email,     setEmail]     = useState("");
  const [password,  setPassword]  = useState("");
  const [password2, setPassword2] = useState("");
  const [showPw,    setShowPw]    = useState(false);
  const [errors,    setErrors]    = useState<Record<string, string>>({});
  const [loading,   setLoading]   = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (password !== password2) errs.password2 = "Passwords do not match.";
    if (password.length < 8)    errs.password  = "Minimum 8 characters.";
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setErrors({});
    setLoading(true);
    try {
      const me = await register({ full_name: fullName, email, password, role });
      toast.success("Account created — welcome aboard!");
      router.push(homeForRole(me.role));
    } catch (err) {
      if (err instanceof APIError && !err.isNetworkError) {
        // Field-level errors live under the structured envelope's
        // error.details, falling back to legacy top-level shape.
        const source =
          (err.data?.error?.details as Record<string, unknown> | undefined) ??
          (err.data && typeof err.data === "object" && !("error" in err.data)
            ? (err.data as Record<string, unknown>)
            : undefined);
        const fe: Record<string, string> = {};
        for (const [k, v] of Object.entries(source ?? {})) {
          if (k === "detail") continue;
          fe[k] = Array.isArray(v) ? String(v[0]) : String(v);
        }
        const message = humanizeError(err);
        setErrors(Object.keys(fe).length ? fe : { _general: message });
        toast.error(message);
      } else {
        const message = humanizeError(err);
        setErrors({ _general: message });
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">

      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[45%] relative overflow-hidden bg-gradient-aurora bg-grid-light flex-col justify-between p-12">
        <div className="absolute inset-0 bg-grid opacity-10" />
        <div className="absolute -top-20 -right-20 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-white/10 blur-3xl" />

        <div className="relative">
          <Link href="/" className="inline-block transition-opacity hover:opacity-80">
            <Logo size={34} tone="light" />
          </Link>
        </div>

        <div className="relative space-y-6">
          <h2 className="text-3xl font-bold tracking-[-0.02em] text-white leading-snug">
            {role === "candidate"
              ? "Start your journey to the right job."
              : "Find top talent in minutes."}
          </h2>
          <p className="text-brand-100/85 leading-relaxed text-md max-w-sm">
            {role === "candidate"
              ? "Create your free account, upload your CV, and get AI-powered job matches instantly."
              : "Post a role and our AI instantly ranks the best-matched candidates from Nepal's talent pool."}
          </p>

          <div className="grid grid-cols-2 gap-3">
            {roleBenefits[role].map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-2.5 rounded-xl border border-white/10 bg-white/10 px-3 py-2.5 backdrop-blur-sm">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white/15">
                  <Icon size={14} className="text-brand-200" />
                </span>
                <span className="text-sm font-medium text-white/90">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-white/50 text-xs">
          Final-year thesis &middot; Coventry University &middot; Nepal
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 bg-[#f8fafc]">
        <div className="w-full max-w-md animate-slide-up">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center justify-center mb-8">
            <Link href="/">
              <Logo size={34} />
            </Link>
          </div>

          <div className="mb-7">
            <h1 className="page-title">Create your account</h1>
            <p className="mt-1 text-sm text-slate-500">Free for all IT graduates and employers in Nepal</p>
          </div>

          {/* Role toggle */}
          <div className="mb-6 grid grid-cols-2 gap-1.5 rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
            {(["candidate", "employer"] as Role[]).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                aria-pressed={role === r}
                className={`flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-all duration-150 ${
                  role === r
                    ? "bg-brand-600 text-white shadow-sm"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                {r === "candidate" ? <User size={14} /> : <Briefcase size={14} />}
                {r === "candidate" ? "Job Seeker" : "Employer"}
              </button>
            ))}
          </div>

          {errors._general && (
            <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-red-200/70 bg-red-50 p-3.5 text-sm text-red-700" role="alert">
              <AlertTriangle size={15} className="mt-0.5 shrink-0 text-red-500" />
              {errors._general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full name</label>
              <div className="relative">
                <User size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  placeholder="Aarav Sharma"
                  className="input pl-9"
                />
              </div>
              {errors.full_name && <p className="mt-1 text-xs text-red-600">{errors.full_name}</p>}
            </div>

            <div>
              <label className="label">Email address</label>
              <div className="relative">
                <Mail size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input pl-9"
                />
              </div>
              {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                  className="input pl-9 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors duration-150"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <PasswordMeter value={password} />
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password}</p>}
            </div>

            <div>
              <label className="label">Confirm password</label>
              <div className="relative">
                <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password2}
                  onChange={e => setPassword2(e.target.value)}
                  placeholder="Re-enter password"
                  className={`input pl-9 ${password2 && password2 !== password ? "!border-red-300 focus:!ring-red-500/15" : ""}`}
                />
              </div>
              {errors.password2 && <p className="mt-1 text-xs text-red-600">{errors.password2}</p>}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center !py-3 !text-md mt-1"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner size={16} />
                  Creating account&hellip;
                </span>
              ) : "Create free account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-brand-600 hover:text-brand-700 transition-colors duration-150">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
