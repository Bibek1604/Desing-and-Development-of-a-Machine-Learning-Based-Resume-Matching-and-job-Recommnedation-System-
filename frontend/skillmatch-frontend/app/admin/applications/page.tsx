"use client";

import { useCallback, useEffect, useState } from "react";
import { Trash2, FileCheck2 } from "lucide-react";
import { admin, humanizeError, type AdminApplication, type Application } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import { AdminHeader, SearchBox, Pager, Badge, TableShell, TableSkeleton, TableError, EmptyRow, Avatar, IconButton } from "@/components/admin/parts";

const STATUSES: Application["status"][] = ["applied", "reviewed", "shortlisted", "rejected"];

export default function AdminApplicationsPage() {
  const toast = useToast();
  const [rows, setRows] = useState<AdminApplication[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    admin.applications.list(page, search, pageSize)
      .then((d) => { setRows(d.results); setCount(d.count); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [page, search, pageSize]);

  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);

  async function changeStatus(a: AdminApplication, status: Application["status"]) {
    try {
      const updated = await admin.applications.update(a.id, status);
      setRows((r) => r.map((x) => (x.id === a.id ? { ...x, status: updated.status } : x)));
      toast.success("Status updated");
    } catch (e) { toast.error(humanizeError(e)); }
  }

  async function remove(a: AdminApplication) {
    if (!confirm("Delete this application?")) return;
    try { await admin.applications.remove(a.id); toast.success("Deleted"); load(); }
    catch (e) { toast.error(humanizeError(e)); }
  }

  return (
    <>
      <AdminHeader title="Applications" subtitle="Candidate applications across all jobs." icon={FileCheck2} accent="amber" />
      <div className="mb-4"><SearchBox value={search} onChange={(v) => { setPage(1); setSearch(v); }} placeholder="Search candidate or job…" /></div>

      {loading ? <TableSkeleton cols={5} /> : error ? (
        <TableError message={humanizeError(error)} onRetry={load} />
      ) : (
        <TableShell head={
          <tr>
            <th className="px-4 py-3">Candidate</th>
            <th className="px-4 py-3">Job</th>
            <th className="px-4 py-3">Match</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Applied</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        }>
          {rows.map((a) => (
            <tr key={a.id} className="transition hover:bg-slate-50/70">
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <Avatar email={a.candidate_email} accent="amber" />
                  <span className="truncate text-slate-700">{a.candidate_email}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-slate-700">{a.job_detail?.title ?? `#${a.job}`}</td>
              <td className="px-4 py-3"><Badge tone={a.match_score >= 60 ? "green" : a.match_score >= 30 ? "amber" : "slate"}>{a.match_score}%</Badge></td>
              <td className="px-4 py-3">
                <select value={a.status} onChange={(e) => changeStatus(a, e.target.value as Application["status"])}
                  className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-semibold capitalize shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
              <td className="px-4 py-3 text-xs text-slate-500">{new Date(a.applied_at).toLocaleDateString()}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end"><IconButton onClick={() => remove(a)} title="Delete" tone="red"><Trash2 size={15} /></IconButton></div>
              </td>
            </tr>
          ))}
          {rows.length === 0 && <EmptyRow colSpan={6} label="No applications found." />}
        </TableShell>
      )}
      <Pager page={page} count={count} pageSize={pageSize} onPage={setPage} onPageSize={(n) => { setPageSize(n); setPage(1); }} />
    </>
  );
}
