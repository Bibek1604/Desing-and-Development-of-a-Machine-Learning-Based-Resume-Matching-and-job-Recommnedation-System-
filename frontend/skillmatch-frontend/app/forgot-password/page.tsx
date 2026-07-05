"use client";

/**
 * /forgot-password
 *
 * Ask for the account email, hand off to the backend, and always show the
 * same "check your inbox" message even if the email is unknown -- that
 * keeps the endpoint from doubling as an account-enumeration oracle.
 */

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Mail, ArrowLeft, CheckCircle2 } from "lucide-react";
import { passwordReset, humanizeError } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import Spinner from "@/components/Spinner";
import Logo from "@/components/Logo";

export default function ForgotPasswordPage() {
  const toast = useToast();
  const [email,   setEmail]   = useState("");
  const [loading, setLoading] = useState(false);
  const [sent,    setSent]    = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await passwordReset.request(email.trim().toLowerCase());
      setSent(true);
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-inner-sm">
        <div className="mb-6">
          <Link href="/login" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900">
            <ArrowLeft size={14} /> Back to sign in
          </Link>
        </div>

        <div className="card p-8 sm:p-10">
          <Logo className="h-9 w-9 mb-4" />
          <h1 className="page-title">Forgot your password?</h1>
          <p className="mt-1 text-sm text-slate-500">
            Enter the email you use on SkillMatch and we&apos;ll send you a link to reset your password.
          </p>

          {sent ? (
            <div className="mt-6 rounded-xl border border-emerald-200/70 bg-emerald-50 p-5 flex items-start gap-3">
              <CheckCircle2 size={18} className="mt-0.5 text-emerald-600 shrink-0" />
              <div>
                <p className="font-semibold text-emerald-800">Check your inbox</p>
                <p className="mt-1 text-sm text-emerald-800">
                  If an account exists for <span className="font-medium">{email}</span>, we&apos;ve sent a password reset link.
                  It expires after a few hours.
                </p>
                <Link href="/login" className="mt-3 inline-block text-sm font-semibold text-emerald-800 underline">
                  Return to sign in
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <label htmlFor="fp-email" className="block text-sm font-semibold text-slate-700">
                Email
              </label>
              <div className="relative">
                <Mail size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  id="fp-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input pl-9"
                />
              </div>
              <button type="submit" disabled={loading || !email} className="btn-primary w-full justify-center !py-2.5">
                {loading ? <Spinner size={14} /> : null}
                {loading ? "Sending…" : "Send reset link"}
              </button>
              <p className="text-2xs text-slate-500 text-center">
                No account?{" "}
                <Link href="/register" className="font-semibold text-brand-600 hover:text-brand-700">
                  Sign up
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
