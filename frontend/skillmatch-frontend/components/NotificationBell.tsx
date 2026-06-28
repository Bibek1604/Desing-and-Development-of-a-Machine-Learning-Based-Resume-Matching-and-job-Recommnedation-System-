"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { Bell, Check } from "lucide-react";
import { notifications as notifApi, type AppNotification } from "@/lib/api";
import { SCORE_THRESHOLDS } from "@/lib/score";

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/** Visual tone for the score circle — aligned with the shared score thresholds. */
function scoreTone(score: number) {
  if (score >= SCORE_THRESHOLDS.high) return "text-brand-700 bg-brand-50 ring-1 ring-inset ring-brand-600/15";
  if (score >= SCORE_THRESHOLDS.mid)  return "text-accent-700 bg-accent-50 ring-1 ring-inset ring-accent-600/15";
  return "text-amber-700 bg-amber-50 ring-1 ring-inset ring-amber-600/15";
}

export default function NotificationBell() {
  const [open,    setOpen]    = useState(false);
  const [notifs,  setNotifs]  = useState<AppNotification[]>([]);
  const [unread,  setUnread]  = useState(0);
  const [highPri, setHighPri] = useState(0);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Poll unread count every 30 seconds
  const fetchCount = useCallback(() => {
    notifApi.unreadCount()
      .then(r => { setUnread(r.unread); setHighPri(r.high_priority); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 30_000);
    return () => clearInterval(interval);
  }, [fetchCount]);

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  async function toggleOpen() {
    if (!open) {
      setLoading(true);
      try {
        const data = await notifApi.list();
        setNotifs(data);
      } catch { /* ignore */ } finally {
        setLoading(false);
      }
    }
    setOpen(v => !v);
  }

  async function handleMarkRead(id: number) {
    await notifApi.markRead(id).catch(() => {});
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    setUnread(c => Math.max(0, c - 1));
  }

  async function handleMarkAllRead() {
    await notifApi.markAllRead().catch(() => {});
    setNotifs(prev => prev.map(n => ({ ...n, is_read: true })));
    setUnread(0);
    setHighPri(0);
  }

  return (
    <div ref={ref} className="relative">
      {/* Bell button */}
      <button
        onClick={toggleOpen}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors duration-150"
        aria-label="Notifications"
      >
        <Bell size={19} strokeWidth={1.9} />

        {/* Unread badge */}
        {unread > 0 && (
          <span className={`absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center
            rounded-full px-1 text-white text-2xs font-bold tabular-nums ring-2 ring-white
            ${highPri > 0 ? "bg-red-500 animate-pulse" : "bg-brand-600"}`}>
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-11 w-96 max-w-[calc(100vw-2rem)] bg-white rounded-xl shadow-pop border border-slate-200/80 z-50 overflow-hidden animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="font-semibold tracking-[-0.01em] text-slate-900 text-sm">Notifications</span>
              {unread > 0 && (
                <span className="px-1.5 py-0.5 bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-600/10 rounded-md text-xs font-medium tabular-nums">
                  {unread} new
                </span>
              )}
            </div>
            {unread > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors duration-150"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-[420px] overflow-y-auto">
            {loading && (
              <div className="space-y-3 p-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i}>
                    <div className="skeleton h-3 w-3/4 mb-2" />
                    <div className="skeleton h-3 w-1/2" />
                  </div>
                ))}
              </div>
            )}

            {!loading && notifs.length === 0 && (
              <div className="py-12 text-center">
                <span className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-400 ring-1 ring-slate-200/70">
                  <Bell size={20} />
                </span>
                <p className="text-slate-500 text-sm">No notifications yet.</p>
                <p className="text-slate-400 text-xs mt-1">Upload your CV to get job matches.</p>
              </div>
            )}

            {!loading && notifs.map(n => {
              const isHP = n.notification_type === "high_priority";
              const score = Math.round(n.match_score);
              return (
                <div
                  key={n.id}
                  onClick={() => !n.is_read && handleMarkRead(n.id)}
                  className={`flex gap-3 px-4 py-3 cursor-pointer transition-colors duration-150 border-b border-slate-50
                    ${n.is_read ? "bg-white hover:bg-slate-50/60" : "bg-brand-50/40 hover:bg-brand-50/70"}
                    ${isHP ? "border-l-2 border-l-red-500" : ""}`}
                >
                  {/* Score badge */}
                  <div className={`shrink-0 flex h-10 w-10 items-center justify-center
                      rounded-full text-sm font-bold tabular-nums ${scoreTone(score)}`}>
                    {score}%
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm font-medium truncate ${n.is_read ? "text-slate-700" : "text-slate-900"}`}>
                        {isHP && <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-red-500 align-middle" aria-label="High priority" />}
                        {n.job_title}
                      </p>
                      <span className="text-xs text-slate-500 shrink-0">{timeAgo(n.sent_at)}</span>
                    </div>
                    <p className="text-xs text-slate-500 truncate">{n.job_company}</p>
                    {n.match_data?.reasons?.length > 0 && (
                      <p className="flex items-center gap-1 text-xs text-brand-700 mt-0.5 truncate">
                        <Check size={11} className="shrink-0" /> {n.match_data.reasons[0]}
                      </p>
                    )}
                    {!n.is_read && (
                      <div className="mt-1 h-1.5 w-1.5 rounded-full bg-brand-500 inline-block" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50/80">
            <Link
              href="/dashboard"
              onClick={() => setOpen(false)}
              className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors duration-150"
            >
              View all matches in Dashboard →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
