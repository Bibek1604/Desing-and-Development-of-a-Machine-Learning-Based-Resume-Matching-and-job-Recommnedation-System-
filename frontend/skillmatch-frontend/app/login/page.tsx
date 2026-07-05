"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, CheckCircle2, AlertTriangle, Sparkles, Mail, Lock } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { humanizeError, homeForRole } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import Logo from "@/components/Logo";
import Spinner from "@/components/Spinner";

/** Only allow single-segment same-origin paths as ?next= targets so the
 * login page can't be turned into an open redirect. */
function safeNext(raw: string | null): string | null {
  if (!raw) return null;
  try {
    const decoded = decodeURIComponent(raw);
    if (!decoded.startsWith("/") || decoded.startsWith("//") || decoded.startsWith("/\\")) {
      return null;
    }
    return decoded;
  } catch {
    return null;
  }
}

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [showPw,   setShowPw]   = useState(false);
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const [nextUrl,  setNextUrl]  = useState<string | null>(null);

  // Read ?next= without pulling in Suspense — parse window.location.search
  // once on mount, then validate the destination.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    setNextUrl(safeNext(params.get("next")));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const me = await login(email, password);
      toast.success("Welcome back!");
      // ?next= wins if present and safe; otherwise fall back to role home.
      router.push(nextUrl || homeForRole(me.role));
    } catch (err) {
      const message = humanizeError(err);
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">

      {/* Left panel — brand */}
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
            Your next role is one upload away.
          </h2>
          <p className="text-brand-100/85 leading-relaxed text-md max-w-sm">
            AI-powered matching for Nepal&apos;s IT graduates. Upload your CV, get instant matches, land the job.
          </p>
          <div className="space-y-3">
            {[
              "ML-powered skills matching",
              "ATS score & resume feedback",
              "Top IT companies in Kathmandu",
            ].map((t) => (
              <div key={t} className="flex items-center gap-2.5 text-sm text-white/90">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/15">
                  <CheckCircle2 size={12} className="text-brand-200" />
                </span>
                {t}
              </div>
            ))}
          </div>

          {/* Mini preview card */}
          <div className="max-w-[280px] rounded-xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="flex items-center gap-1.5 text-xs font-semibold text-white/90">
                <Sparkles size={12} className="text-brand-200" /> Match found
              </span>
              <span className="rounded-md bg-brand-400/25 px-1.5 py-0.5 text-2xs font-bold tabular-nums text-brand-100">92%</span>
            </div>
            <p className="text-sm font-semibold text-white">Junior ML Engineer</p>
            <p className="text-xs text-white/60 mt-0.5">Fusemachines · Kathmandu</p>
            <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/15">
              <div className="h-full w-[92%] rounded-full bg-gradient-to-r from-brand-300 to-accent-300" />
            </div>
          </div>
        </div>

        <div className="relative">
          <p className="text-white/50 text-xs">
            Final-year thesis project &middot; Coventry University &middot; Nepal
          </p>
        </div>
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

          <div className="mb-8">
            <h1 className="page-title">Welcome back</h1>
            <p className="mt-1 text-sm text-slate-500">Sign in to your account to continue</p>
          </div>

          {error && (
            <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-red-200/70 bg-red-50 p-3.5 text-sm text-red-700" role="alert">
              <AlertTriangle size={15} className="mt-0.5 shrink-0 text-red-500" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
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
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="label !mb-0">Password</label>
                <Link
                  href="/forgot-password"
                  className="text-2xs font-semibold text-brand-600 hover:text-brand-700"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
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
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center !py-3 !text-md mt-2"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner size={16} />
                  Signing in&hellip;
                </span>
              ) : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-semibold text-brand-600 hover:text-brand-700 transition-colors duration-150">
              Create one free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
