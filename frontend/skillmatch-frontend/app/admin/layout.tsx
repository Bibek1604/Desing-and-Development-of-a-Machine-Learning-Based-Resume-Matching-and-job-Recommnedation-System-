"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard, Users, Briefcase, FileCheck2, Tags, FileText,
  ArrowUpRight, LogOut, Menu, X,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { LogoMark } from "@/components/Logo";
import Spinner from "@/components/Spinner";

const nav = [
  { href: "/admin",              label: "Dashboard",    icon: LayoutDashboard, exact: true, accent: "text-brand-600 bg-brand-50" },
  { href: "/admin/users",        label: "Users",        icon: Users,                        accent: "text-sky-600 bg-sky-50" },
  { href: "/admin/jobs",         label: "Jobs",         icon: Briefcase,                    accent: "text-violet-600 bg-violet-50" },
  { href: "/admin/applications", label: "Applications", icon: FileCheck2,                   accent: "text-amber-600 bg-amber-50" },
  { href: "/admin/skills",       label: "Skills",       icon: Tags,                         accent: "text-teal-600 bg-teal-50" },
  { href: "/admin/resumes",      label: "Resumes",      icon: FileText,                     accent: "text-rose-600 bg-rose-50" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) { window.location.href = "/login"; return; }
    if (!isAdmin) { window.location.href = "/"; }
  }, [isLoading, isAuthenticated, isAdmin]);

  useEffect(() => { setOpen(false); }, [pathname]);

  if (isLoading || !isAuthenticated || !isAdmin) {
    return <div className="flex min-h-screen items-center justify-center"><Spinner size={28} /></div>;
  }

  const isActive = (href: string, exact?: boolean) => (exact ? pathname === href : pathname.startsWith(href));
  const current = [...nav].sort((a, b) => b.href.length - a.href.length).find((n) => isActive(n.href, n.exact));
  const initials = (user?.full_name || user?.email || "A").slice(0, 1).toUpperCase();

  const SidebarInner = (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <Link href="/" className="flex items-center gap-2.5 px-5 py-5">
        <LogoMark size={32} />
        <span className="leading-tight">
          <span className="block text-sm font-bold tracking-[-0.02em] text-white">SkillMatch</span>
          <span className="block text-2xs font-medium uppercase tracking-[0.16em] text-brand-200/80">Admin Console</span>
        </span>
      </Link>

      <div className="mx-5 mb-3 rule-fade opacity-40" />

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3">
        {nav.map(({ href, label, icon: Icon, exact, accent }) => {
          const active = isActive(href, exact);
          return (
            <Link
              key={href}
              href={href}
              className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                active ? "bg-white/10 text-white" : "text-brand-100/70 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span className={`flex h-7 w-7 items-center justify-center rounded-lg transition ${active ? accent : "bg-white/5 text-brand-100/70 group-hover:text-white"}`}>
                <Icon size={15} />
              </span>
              {label}
              {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-300" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer / user */}
      <div className="mt-auto p-3">
        <Link href="/" className="mb-1 flex items-center gap-2 rounded-xl px-3 py-2 text-2xs font-semibold uppercase tracking-wide text-brand-100/60 transition hover:bg-white/5 hover:text-white">
          <ArrowUpRight size={13} /> Back to site
        </Link>
        <div className="flex items-center gap-2.5 rounded-xl bg-white/5 px-3 py-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-accent-500 text-xs font-bold text-white">{initials}</span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-white">{user?.full_name || "Admin"}</p>
            <p className="truncate text-2xs text-brand-100/60">{user?.email}</p>
          </div>
          <button onClick={logout} title="Log out" className="rounded-lg p-1.5 text-brand-100/60 transition hover:bg-white/10 hover:text-white">
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#f6f8fb]">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 overflow-hidden bg-gradient-aurora bg-grid-light md:block">
        {SidebarInner}
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 overflow-hidden bg-gradient-aurora bg-grid-light animate-slide-in-right">
            <button onClick={() => setOpen(false)} className="absolute right-3 top-4 rounded-lg p-1.5 text-white/70 hover:bg-white/10"><X size={18} /></button>
            {SidebarInner}
          </aside>
        </div>
      )}

      {/* Main column */}
      <div className="md:pl-64">
        {/* Topbar */}
        <header className="sticky top-0 z-30 border-b border-slate-200/70 glass">
          <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
            <button onClick={() => setOpen(true)} className="rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 md:hidden"><Menu size={20} /></button>
            <nav className="flex items-center gap-1.5 text-sm">
              <span className="text-slate-400">Admin</span>
              <span className="text-slate-300">/</span>
              <span className="font-semibold text-slate-800">{current?.label ?? "Dashboard"}</span>
            </nav>
            <span className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-1 text-2xs font-semibold text-brand-700 ring-1 ring-inset ring-brand-600/15">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-500" /> Administrator
            </span>
          </div>
        </header>

        {/* Page content over a soft mesh */}
        <main className="bg-mesh min-h-[calc(100vh-3.5rem)] px-4 py-7 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl animate-fade-in">{children}</div>
        </main>
      </div>
    </div>
  );
}
