"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, Pencil, Tags } from "lucide-react";
import { admin, humanizeError } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import { AdminHeader, SearchBox, Pager, Modal, Badge, TableShell, TableSkeleton, TableError, EmptyRow, IconButton } from "@/components/admin/parts";
import Spinner from "@/components/Spinner";

interface Skill { id: number; name: string; slug: string; category: string }
type FormState = { id?: number; name: string; category: string };
const EMPTY: FormState = { name: "", category: "" };

export default function AdminSkillsPage() {
  const toast = useToast();
  const [rows, setRows] = useState<Skill[]>([]);
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
    admin.skills.list(page, search, pageSize)
      .then((d) => { setRows(d.results); setCount(d.count); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [page, search, pageSize]);

  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);

  function openCreate() { setForm(EMPTY); setModalOpen(true); }
  function openEdit(s: Skill) { setForm({ id: s.id, name: s.name, category: s.category }); setModalOpen(true); }

  async function save() {
    setSaving(true);
    try {
      if (form.id) { await admin.skills.update(form.id, { name: form.name, category: form.category }); toast.success("Skill updated"); }
      else { await admin.skills.create({ name: form.name, category: form.category }); toast.success("Skill created"); }
      setModalOpen(false); load();
    } catch (e) { toast.error(humanizeError(e)); }
    finally { setSaving(false); }
  }

  async function remove(s: Skill) {
    if (!confirm(`Delete skill "${s.name}"?`)) return;
    try { await admin.skills.remove(s.id); toast.success("Skill deleted"); load(); }
    catch (e) { toast.error(humanizeError(e)); }
  }

  return (
    <>
      <AdminHeader
        title="Skills" subtitle="The matching vocabulary used to score resumes and jobs." icon={Tags} accent="teal"
        action={<button onClick={openCreate} className="btn-primary !py-2 !text-sm"><Plus size={15} /> Add skill</button>}
      />
      <div className="mb-4"><SearchBox value={search} onChange={(v) => { setPage(1); setSearch(v); }} placeholder="Search skill…" /></div>

      {loading ? <TableSkeleton cols={3} /> : error ? (
        <TableError message={humanizeError(error)} onRetry={load} />
      ) : (
        <TableShell head={
          <tr>
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3">Category</th>
            <th className="px-4 py-3">Slug</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        }>
          {rows.map((s) => (
            <tr key={s.id} className="transition hover:bg-slate-50/70">
              <td className="px-4 py-3 font-medium text-slate-800">{s.name}</td>
              <td className="px-4 py-3">{s.category ? <Badge tone="teal">{s.category}</Badge> : <span className="text-slate-400">—</span>}</td>
              <td className="px-4 py-3 text-xs text-slate-500">{s.slug}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-1">
                  <IconButton onClick={() => openEdit(s)} title="Edit"><Pencil size={15} /></IconButton>
                  <IconButton onClick={() => remove(s)} title="Delete" tone="red"><Trash2 size={15} /></IconButton>
                </div>
              </td>
            </tr>
          ))}
          {rows.length === 0 && <EmptyRow colSpan={4} label="No skills found." />}
        </TableShell>
      )}
      <Pager page={page} count={count} pageSize={pageSize} onPage={setPage} onPageSize={(n) => { setPageSize(n); setPage(1); }} />

      <Modal open={modalOpen} title={form.id ? "Edit skill" : "Add skill"} onClose={() => setModalOpen(false)}>
        <div className="space-y-3">
          <div><label className="label">Name</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Django" /></div>
          <div><label className="label">Category</label><input className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="e.g. Backend" /></div>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setModalOpen(false)} className="btn-outline !py-2 !text-sm">Cancel</button>
            <button onClick={save} disabled={saving || !form.name} className="btn-primary !py-2 !text-sm">{saving ? <Spinner size={15} /> : "Save"}</button>
          </div>
        </div>
      </Modal>
    </>
  );
}
