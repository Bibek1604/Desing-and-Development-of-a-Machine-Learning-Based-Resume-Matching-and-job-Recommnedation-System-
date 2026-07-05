"use client";

/**
 * EmailVerifyBanner — shown at the top of the dashboard when the current
 * candidate hasn't confirmed their email yet. Includes a "Resend" button
 * that hits POST /api/auth/verify-email/send/.
 */

import { useState } from "react";
import { MailWarning, Send } from "lucide-react";
import { emailVerification, humanizeError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import Spinner from "@/components/Spinner";

export default function EmailVerifyBanner() {
  const { user } = useAuth();
  const toast = useToast();
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  if (!user) return null;
  // `email_verified` is optional on the type so an older backend response
  // (no field yet) is treated as verified — never nag a user we can't check.
  if (user.email_verified !== false) return null;

  async function resend() {
    setSending(true);
    try {
      await emailVerification.send();
      setSent(true);
      toast.success("Verification email sent");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200/70 bg-amber-50 p-4">
      <MailWarning size={18} className="mt-0.5 shrink-0 text-amber-600" />
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-amber-900">Confirm your email address</p>
        <p className="mt-0.5 text-sm text-amber-800">
          {sent
            ? "We just sent a fresh verification link — check your inbox."
            : <>We sent a verification link to <span className="font-medium">{user.email}</span>. Confirm it to unlock everything on SkillMatch.</>}
        </p>
      </div>
      <button
        type="button"
        onClick={resend}
        disabled={sending || sent}
        className="btn-outline shrink-0 !py-1.5 !px-3 !text-xs"
      >
        {sending ? <Spinner size={12} /> : <Send size={12} />}
        {sending ? "Sending…" : sent ? "Sent" : "Resend"}
      </button>
    </div>
  );
}
