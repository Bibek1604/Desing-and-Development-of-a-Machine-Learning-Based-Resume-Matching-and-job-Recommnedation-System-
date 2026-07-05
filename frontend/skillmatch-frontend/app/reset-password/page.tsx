"use client";

/**
 * /reset-password?uid=<>&token=<>
 *
 * Reads the signed uid + token from the URL (produced by the backend
 * PasswordResetTokenGenerator), collects a new password, POSTs to the
 * confirm endpoint. On success, the user goes to /login and can sign in.
 */

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { Lock, Eye, EyeOff, CheckCircle2, AlertTriangle } from "lucide-react";
import { passwordReset, humanizeError } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import Spinner from "@/components/Spinner";
import Logo from "@/components/Logo";

export default function ResetPasswordPage() {
  const toast = useToast();
  const [uid,      setUid]      = useState("");
  const [token,    setToken]    = useState("");
  const [password, setPassword] = useState("");
  const [confirm,  setConfirm]  = useState("");
  const [show,     setShow]     = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [done,     setDone]     = useState(false);
  const [error,    setError]    = useState("");

  // Pull uid + token off the URL once, on mount.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const p = new URLSearchParams(window.location.search);
    setUid(p.get("uid") ?? "");
    setToken(p.get("token") ?? "");
  }, []);

  const linkOk = uid && token;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await passwordReset.confirm(uid, token, password);
      setDone(true);
      toast.success("Password updated");
    } catch (err) {
      const msg = humanizeError(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-inner-sm">
        <div className="card p-8 sm:p-10">
          <Logo className="h-9 w-9 mb-4" />
          <h1 className="page-title">Reset your password</h1>
          {!linkOk ? (
            <div className="mt-4 rounded-lg border border-amber-200/70 bg-amber-50 p-4 text-sm text-amber-800 flex items-start gap-2">
              <AlertTriangle size={15} className="mt-0.5 shrink-0" />
              <span>This link is missing information. Please request a new one from{" "}
                <Link href="/forgot-password" className="underline font-semibold">Forgot password</Link>.
              </span>
            </div>
          ) : done ? (
            <div className="mt-6 rounded-xl border border-emerald-200/70 bg-emerald-50 p-5 flex items-start gap-3">
              <CheckCircle2 size={18} className="mt-0.5 text-emerald-600 shrink-0" />
              <div>
                <p className="font-semibold text-emerald-800">Password updated</p>
                <p className="mt-1 text-sm text-emerald-800">
                  You can sign in with your new password now.
                </p>
                <Link href="/login" className="btn-primary mt-4 !py-2 !px-4 !text-sm">
                  Sign in
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <p className="text-sm text-slate-500">Choose a new password. At least 8 characters.</p>
              {error && (
                <div className="flex items-start gap-2 rounded-lg border border-red-200/70 bg-red-50 p-3 text-sm text-red-700" role="alert">
                  <AlertTriangle size={14} className="mt-0.5 shrink-0" /> {error}
                </div>
              )}

              <div>
                <label htmlFor="rp-pw" className="block text-sm font-semibold text-slate-700 mb-1.5">New password</label>
                <div className="relative">
                  <Lock size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    id="rp-pw"
                    type={show ? "text" : "password"}
                    required minLength={8}
                    autoComplete="new-password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="input pl-9 pr-10"
                  />
                  <button type="button" onClick={() => setShow(s => !s)} aria-label={show ? "Hide password" : "Show password"}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                    {show ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="rp-pw2" className="block text-sm font-semibold text-slate-700 mb-1.5">Confirm new password</label>
                <div className="relative">
                  <Lock size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    id="rp-pw2"
                    type={show ? "text" : "password"}
                    required minLength={8}
                    autoComplete="new-password"
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    className="input pl-9"
                  />
                </div>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center !py-2.5">
                {loading ? <Spinner size={14} /> : null}
                {loading ? "Saving…" : "Update password"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
