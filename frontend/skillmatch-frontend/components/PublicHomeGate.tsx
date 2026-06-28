"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { homeForRole } from "@/lib/api";

/**
 * Wraps the public landing page. Logged-in users never see the global
 * homepage — they're redirected to their own section's home (candidates →
 * /dashboard, employers → /employer, admins → /admin). Only logged-out
 * visitors see the marketing content.
 */
export default function PublicHomeGate({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      router.replace(homeForRole(user.role));
    }
  }, [isLoading, isAuthenticated, user, router]);

  // Children still render (so logged-out visitors and crawlers get the full
  // marketing page), but while the session resolves or a logged-in user is
  // being redirected, an opaque overlay hides it — so a signed-in user never
  // sees the global homepage flash before landing in their own section.
  const covering = isLoading || isAuthenticated;

  return (
    <>
      {children}
      {covering && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-[#f8fafc]">
          <div
            className="h-8 w-8 rounded-full border-2 border-brand-600 border-t-transparent animate-spin"
            role="status"
            aria-label="Loading"
          />
        </div>
      )}
    </>
  );
}
