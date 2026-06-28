"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, Pencil, Briefcase } from "lucide-react";
import { admin, humanizeError, type Job, type JobCreatePayload } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import { AdminHeader, SearchBox, Pager, Modal, Badge, TableShell, TableSkeleton, TableError, EmptyRow, IconButton } from "@/components/admin/parts";
import Spinner from "@/components/Spinner";

const JOB_TYPES = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "internship", label: "Internship" },
  { value: "contract", label: "Contract" },
];

type FormState = JobCreatePayload & { id?: number; is_active: boolean };
const EMPTY: FormState = { title: "", company: "", location: "", job_type: "full_time", description: "", requirements: "", is_active: true };

export default function AdminJobsPage() {
  const toast = useToast();
  const [rows, setRows] = useState<Job[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    admin.jobs.list(page, search, pageSize)
      .then((d) => { setRows(d.results); setCount(d.count); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [page, search, pageSize]);

  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);

  function openCreate() { setForm(EMPTY); setModalOpen(true); }
  function openEdit(j: Job) {
    setForm({ id: j.id, title: j.title, company: j.company, location: j.location, job_type: j.job_type, description: j.description, requirements: j.requirements, salary_min: j.salary_min, salary_max: j.salary_max, is_active: j.is_active });
    setModalOpen(true);
  }

  async function save() {
    setSaving(true);
    try {
      const { id, ...payload } = form;
      if (id) { await admin.jobs.update(id, payload); toast.success("Job updated"); }
      else { await admin.jobs.create(payload); toast.success("Job created"); }
      setModalOpen(false); load();
    } catch (e) { toast.error(humanizeError(e)); }
    finally { setSaving(false); }
  }

  async function remove(j: Job) {
    if (!confirm(`Delete "${j.title}"?`)) return;
    try { await admin.jobs.remove(j.id); toast.success("Job deleted"); load(); }
    catch (e) { toast.error(humanizeError(e)); }
  }

  return (
    <>
      <AdminHeader
        title="Jobs" subtitle="Every posting on the platform." icon={Briefcase} accent="violet"
        action={<button onClick={openCreate} className="btn-primary !py-2 !text-sm"><Plus size={15} /> Add job</button>}
      />
      <div className="mb-4"><SearchBox value={search} onChange={(v) => { setPage(1); setSearch(v); }} placeholder="Search title, company…" /></div>

      {loading ? <TableSkeleton cols={4} /> : error ? (
        <TableError message={humanizeError(error)} onRetry={load} />
      ) : (
        <TableShell head={
          <tr>
            <th className="px-4 py-3">Title</th>
            <th className="px-4 py-3">Company</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        }>
          {rows.map((j) => (
            <tr key={j.id} className="transition hover:bg-slate-50/70">
              <td className="px-4 py-3 font-medium text-slate-800">{j.title}</td>
              <td className="px-4 py-3 text-slate-600">{j.company || "—"}</td>
              <td className="px-4 py-3"><Badge tone="violet">{JOB_TYPES.find((t) => t.value === j.job_type)?.label ?? j.job_type}</Badge></td>
              <td className="px-4 py-3"><Badge tone={j.is_active ? "green" : "slate"} dot>{j.is_active ? "active" : "closed"}</Badge></td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-1">
                  <IconButton onClick={() => openEdit(j)} title="Edit"><Pencil size={15} /></IconButton>
                  <IconButton onClick={() => remove(j)} title="Delete" tone="red"><Trash2 size={15} /></IconButton>
                </div>
              </td>
            </tr>
          ))}
          {rows.length === 0 && <EmptyRow colSpan={5} label="No jobs found." />}
        </TableShell>
      )}
      <Pager page={page} count={count} pageSize={pageSize} onPage={setPage} onPageSize={(n) => { setPageSize(n); setPage(1); }} />

      <Modal open={modalOpen} title={form.id ? "Edit job" : "Add job"} onClose={() => setModalOpen(false)}>
        <div className="space-y-3">
          <div><label className="label">Title</label><input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Company</label><input className="input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></div>
            <div><label className="label">Location</label><input className="input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /></div>
          </div>
          <div>
            <label className="label">Type</label>
            <select className="input" value={form.job_type} onChange={(e) => setForm({ ...form, job_type: e.target.value })}>
              {JOB_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div><label className="label">Description</label><textarea className="input min-h-[80px]" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Salary min</label><input className="input" type="number" value={form.salary_min ?? ""} onChange={(e) => setForm({ ...form, salary_min: e.target.value ? Number(e.target.value) : undefined })} /></div>
            <div><label className="label">Salary max</label><input className="input" type="number" value={form.salary_max ?? ""} onChange={(e) => setForm({ ...form, salary_max: e.target.value ? Number(e.target.value) : undefined })} /></div>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Active
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setModalOpen(false)} className="btn-outline !py-2 !text-sm">Cancel</button>
            <button onClick={save} disabled={saving || !form.title || !form.description} className="btn-primary !py-2 !text-sm">{saving ? <Spinner size={15} /> : "Save"}</button>
          </div>
        </div>
      </Modal>
    </>
  );
}
