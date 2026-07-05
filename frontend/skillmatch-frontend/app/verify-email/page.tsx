"use client";

/**
 * /verify-email?uid=<>&token=<>
 *
 * Confirms the user's email address. The page reads uid + token from the URL,
 * POSTs to the backend confirm endpoint, and shows one of three states:
 * "verifying", "success", or "error".
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, AlertTriangle, Mail } from "lucide-react";
import { emailVerification, humanizeError } from "@/lib/api";
import Spinner from "@/components/Spinner";
import Logo from "@/components/Logo";

type State = "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const [state, setState] = useState<State>("loading");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const p = new URLSearchParams(window.location.search);
    const uid = p.get("uid") ?? "";
    const token = p.get("token") ?? "";
    if (!uid || !token) {
      setError("This verification link is missing information.");
      setState("error");
      return;
    }
    emailVerification.confirm(uid, token)
      .then((res) => {
        setEmail(res.email ?? "");
        setState("success");
      })
      .catch((err) => {
        setError(humanizeError(err));
        setState("error");
      });
  }, []);

  return (
    <div className="page">
      <div className="page-inner-sm">
        <div className="card p-8 sm:p-10 text-center">
          <Logo className="h-9 w-9 mx-auto mb-4" />
          {state === "loading" && (
            <>
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 mb-4">
                <Spinner size={20} />
              </div>
              <h1 className="page-title">Verifying your email…</h1>
              <p className="mt-1 text-sm text-slate-500">Hold tight, this only takes a moment.</p>
            </>
          )}
          {state === "success" && (
            <>
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 mb-4">
                <CheckCircle2 size={22} className="text-emerald-600" />
              </div>
              <h1 className="page-title">Email verified</h1>
              <p className="mt-1 text-sm text-slate-500">
                {email
                  ? <>Thanks — <span className="font-medium">{email}</span> is confirmed. You&apos;re all set.</>
                  : "Thanks — your address is confirmed. You're all set."}
              </p>
              <Link href="/dashboard" className="btn-primary mt-6 !py-2 !px-4 !text-sm">
                Go to dashboard
              </Link>
            </>
          )}
          {state === "error" && (
            <>
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 mb-4">
                <AlertTriangle size={22} className="text-amber-600" />
              </div>
              <h1 className="page-title">We couldn&apos;t verify that link</h1>
              <p className="mt-1 text-sm text-slate-500">{error || "The link is invalid or expired."}</p>
              <div className="mt-6 flex items-center justify-center gap-3">
                <Link href="/dashboard" className="btn-outline !py-2 !px-4 !text-sm">
                  <Mail size={13} /> Try resending
                </Link>
                <Link href="/login" className="btn-ghost !py-2 !px-4 !text-sm">
                  Back to sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
