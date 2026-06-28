"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, X, Brain, LogOut, User, Briefcase } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import NotificationBell from "@/components/NotificationBell";
import Logo from "@/components/Logo";

const candidateLinks = [
  { href: "/recommended", label: "Recommended" },
  { href: "/jobs",        label: "All Jobs" },
  { href: "/dashboard",   label: "Dashboard" },
  { href: "/applications", label: "Applications" },
  { href: "/profile",     label: "Profile" },
];

const employerLinks = [
  { href: "/employer", label: "Post Jobs" },
];

const adminLinks = [
  { href: "/admin", label: "Admin Panel" },
];

const publicLinks = [
  { href: "/jobs",     label: "Find Jobs" },
  { href: "/employer", label: "For Employers" },
];

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  const isEmployer = user?.role === "employer";
  const isAdmin = user?.role === "admin";
  const navLinks = !isAuthenticated
    ? publicLinks
    : isAdmin
    ? adminLinks
    : isEmployer
    ? employerLinks
    : candidateLinks;

  const initials = user?.full_name
    ? user.full_name.split(" ").slice(0, 2).map((n: string) => n[0]).join("").toUpperCase()
    : user?.email?.[0]?.toUpperCase() ?? "?";

  function handleLogout() {
    logout();
    setOpen(false);
    // Hard navigation: guarantees a clean reset and avoids a race with any
    // protected page's auth guard, so logout always works from any screen.
    window.location.assign("/");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/60 glass">
      <nav className="container-px flex h-16 items-center justify-between">

        {/* Logo */}
        <Link
          href="/"
          className="group transition-opacity hover:opacity-80"
          onClick={() => setOpen(false)}
        >
          <Logo size={30} />
        </Link>

        {/* Desktop nav links */}
        <div className="hidden items-center gap-0.5 md:flex">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={isActive(l.href) ? "page" : undefined}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150 ${
                isActive(l.href)
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-600 hover:bg-slate-100/80 hover:text-slate-900"
              }`}
            >
              {l.label}
            </Link>
          ))}
          {isAuthenticated && !isEmployer && !isAdmin && (
            <Link
              href="/dashboard/ai-insights"
              className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-brand-600 transition-colors duration-150 hover:bg-brand-50"
            >
              <Brain size={14} />
              AI Insights
            </Link>
          )}
        </div>

        {/* Desktop auth */}
        <div className="hidden items-center gap-2 md:flex">
          {isAuthenticated ? (
            <>
              {!isEmployer && !isAdmin && <NotificationBell />}
              <span className="hidden lg:block text-sm text-slate-500 max-w-[140px] truncate">
                {user?.full_name ?? user?.email}
              </span>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-brand text-white text-xs font-bold shadow-sm">
                {initials}
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 hover:bg-red-50 hover:text-red-600 transition"
              >
                <LogOut size={15} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-brand-700 transition"
              >
                Sign in
              </Link>
              <Link href="/register" className="btn-primary !py-2 !text-xs !px-4">
                Get Started
              </Link>
            </>
          )}
        </div>

        {/* Mobile burger */}
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 md:hidden transition"
          aria-label="Toggle menu"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </nav>

      {/* Mobile menu */}
      {open && (
        <div className="border-t border-slate-100 bg-white/95 backdrop-blur md:hidden animate-fade-in">
          <div className="container-px flex flex-col gap-1 py-3">
            {navLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                aria-current={isActive(l.href) ? "page" : undefined}
                className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive(l.href)
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-700 hover:bg-brand-50 hover:text-brand-700"
                }`}
              >
                {l.href.startsWith("/jobs") ? <Briefcase size={15} /> : l.href === "/profile" ? <User size={15} /> : null}
                {l.label}
              </Link>
            ))}
            {isAuthenticated && !isEmployer && !isAdmin && (
              <Link
                href="/dashboard/ai-insights"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-brand-600 hover:bg-brand-50 transition"
              >
                <Brain size={15} />
                AI Insights
              </Link>
            )}
            <div className="mt-2 pt-2 border-t border-slate-100 flex flex-col gap-2">
              {isAuthenticated ? (
                <>
                  <div className="flex items-center gap-2.5 px-3 py-2">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-white text-xs font-bold">
                      {initials}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{user?.full_name ?? user?.email}</p>
                      <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center justify-center gap-2 rounded-xl border border-red-100 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 transition"
                  >
                    <LogOut size={15} />
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setOpen(false)}
                    className="btn-outline justify-center py-2.5"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    onClick={() => setOpen(false)}
                    className="btn-primary justify-center py-2.5"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
