"use client";

import { useCallback, useEffect, useState } from "react";
import { Trash2, FileText, Eye } from "lucide-react";
import { admin, mediaUrl, humanizeError, type AdminResume } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import { AdminHeader, SearchBox, Pager, Badge, TableShell, TableSkeleton, TableError, EmptyRow, Avatar, IconButton, Modal } from "@/components/admin/parts";

function skillCount(r: AdminResume): number {
  return Array.isArray(r.extracted_skills) ? r.extracted_skills.length : 0;
}

export default function AdminResumesPage() {
  const toast = useToast();
  const [rows, setRows] = useState<AdminResume[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);
  const [viewing, setViewing] = useState<AdminResume | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    admin.resumes.list(page, search, pageSize)
      .then((d) => { setRows(d.results); setCount(d.count); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [page, search, pageSize]);

  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);

  async function remove(r: AdminResume) {
    if (!confirm(`Delete resume "${r.original_filename}"?`)) return;
    try { await admin.resumes.remove(r.id); toast.success("Resume deleted"); load(); }
    catch (e) { toast.error(humanizeError(e)); }
  }

  return (
    <>
      <AdminHeader title="Resumes" subtitle="All uploaded resumes." icon={FileText} accent="rose" />
      <div className="mb-4"><SearchBox value={search} onChange={(v) => { setPage(1); setSearch(v); }} placeholder="Search candidate or file…" /></div>

      {loading ? <TableSkeleton cols={5} /> : error ? (
        <TableError message={humanizeError(error)} onRetry={load} />
      ) : (
        <TableShell head={
          <tr>
            <th className="px-4 py-3">Candidate</th>
            <th className="px-4 py-3">File</th>
            <th className="px-4 py-3">Skills</th>
            <th className="px-4 py-3">Primary</th>
            <th className="px-4 py-3">Uploaded</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        }>
          {rows.map((r) => (
            <tr key={r.id} className="transition hover:bg-slate-50/70">
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <Avatar email={r.candidate_email} accent="rose" />
                  <span className="truncate text-slate-700">{r.candidate_email}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-slate-600">{r.original_filename || "—"}</td>
              <td className="px-4 py-3 tabular-nums text-slate-600">{skillCount(r)}</td>
              <td className="px-4 py-3">{r.is_primary ? <Badge tone="green" dot>primary</Badge> : <span className="text-slate-400">—</span>}</td>
              <td className="px-4 py-3 text-xs text-slate-500">{new Date(r.uploaded_at).toLocaleDateString()}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-1">
                  <IconButton onClick={() => setViewing(r)} title="View resume"><Eye size={15} /></IconButton>
                  <IconButton onClick={() => remove(r)} title="Delete" tone="red"><Trash2 size={15} /></IconButton>
                </div>
              </td>
            </tr>
          ))}
          {rows.length === 0 && <EmptyRow colSpan={6} label="No resumes found." />}
        </TableShell>
      )}
      <Pager page={page} count={count} pageSize={pageSize} onPage={setPage} onPageSize={(n) => { setPageSize(n); setPage(1); }} />

      <Modal
        open={!!viewing}
        title={viewing?.candidate_email ?? "Resume"}
        subtitle={viewing?.original_filename || undefined}
        onClose={() => setViewing(null)}
      >
        {viewing && (
          <div className="space-y-3">
            {viewing.file && (
              <a href={mediaUrl(viewing.file) ?? "#"} target="_blank" rel="noopener noreferrer"
                className="inline-block text-xs font-semibold text-brand-600 hover:text-brand-700">
                Download original file
              </a>
            )}
            <pre className="whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-4 text-xs leading-relaxed text-slate-700 max-h-[60vh] overflow-y-auto">
              {viewing.raw_text || "No parsed text available."}
            </pre>
          </div>
        )}
      </Modal>
    </>
  );
}
