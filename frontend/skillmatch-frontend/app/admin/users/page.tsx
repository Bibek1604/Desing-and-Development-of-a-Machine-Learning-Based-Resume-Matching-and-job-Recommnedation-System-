"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, Pencil, Users } from "lucide-react";
import { admin, humanizeError, type AdminUser, type UserRole } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import { AdminHeader, SearchBox, Pager, Modal, Badge, TableShell, TableSkeleton, TableError, EmptyRow, Avatar, IconButton } from "@/components/admin/parts";
import Spinner from "@/components/Spinner";

const ROLE_TONE: Record<UserRole, "blue" | "violet" | "amber"> = { candidate: "blue", employer: "violet", admin: "amber" };
const ROLE_ACCENT: Record<UserRole, "sky" | "violet" | "amber"> = { candidate: "sky", employer: "violet", admin: "amber" };

type FormState = { id?: number; email: string; full_name: string; role: UserRole; password: string; is_active: boolean };
const EMPTY: FormState = { email: "", full_name: "", role: "candidate", password: "", is_active: true };

export default function AdminUsersPage() {
  const toast = useToast();
  const [rows, setRows] = useState<AdminUser[]>([]);
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
    admin.users.list(page, search, pageSize)
      .then((d) => { setRows(d.results); setCount(d.count); })
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [page, search, pageSize]);

  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); }, [load]);

  function openCreate() { setForm(EMPTY); setModalOpen(true); }
  function openEdit(u: AdminUser) {
    setForm({ id: u.id, email: u.email, full_name: u.full_name, role: u.role, password: "", is_active: u.is_active });
    setModalOpen(true);
  }

  async function save() {
    setSaving(true);
    try {
      if (form.id) {
        await admin.users.update(form.id, { full_name: form.full_name, role: form.role, is_active: form.is_active, ...(form.password ? { password: form.password } : {}) });
        toast.success("User updated");
      } else {
        await admin.users.create({ email: form.email, full_name: form.full_name, role: form.role, password: form.password || undefined, is_active: form.is_active });
        toast.success("User created");
      }
      setModalOpen(false); load();
    } catch (e) { toast.error(humanizeError(e)); }
    finally { setSaving(false); }
  }

  async function remove(u: AdminUser) {
    if (!confirm(`Delete ${u.email}? This cannot be undone.`)) return;
    try { await admin.users.remove(u.id); toast.success("User deleted"); load(); }
    catch (e) { toast.error(humanizeError(e)); }
  }

  return (
    <>
      <AdminHeader
        title="Users" subtitle="Candidates, employers, and admins." icon={Users} accent="sky"
        action={<button onClick={openCreate} className="btn-primary !py-2 !text-sm"><Plus size={15} /> Add user</button>}
      />
      <div className="mb-4"><SearchBox value={search} onChange={(v) => { setPage(1); setSearch(v); }} placeholder="Search email or name…" /></div>

      {loading ? <TableSkeleton cols={5} /> : error ? (
        <TableError message={humanizeError(error)} onRetry={load} />
      ) : (
        <TableShell head={
          <tr>
            <th className="px-4 py-3">User</th>
            <th className="px-4 py-3">Role</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Skills</th>
            <th className="px-4 py-3">Joined</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        }>
          {rows.map((u) => (
            <tr key={u.id} className="transition hover:bg-slate-50/70">
              <td className="px-4 py-3">
                <div className="flex items-center gap-3">
                  <Avatar name={u.full_name} email={u.email} accent={ROLE_ACCENT[u.role]} />
                  <div className="min-w-0">
                    <p className="truncate font-medium text-slate-800">{u.full_name || "—"}</p>
                    <p className="truncate text-xs text-slate-500">{u.email}</p>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3"><Badge tone={ROLE_TONE[u.role]} dot>{u.role}</Badge></td>
              <td className="px-4 py-3"><Badge tone={u.is_active ? "green" : "red"} dot>{u.is_active ? "active" : "inactive"}</Badge></td>
              <td className="px-4 py-3 tabular-nums text-slate-600">{u.skills_count}</td>
              <td className="px-4 py-3 text-xs text-slate-500">{new Date(u.date_joined).toLocaleDateString()}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-1">
                  <IconButton onClick={() => openEdit(u)} title="Edit"><Pencil size={15} /></IconButton>
                  <IconButton onClick={() => remove(u)} title="Delete" tone="red"><Trash2 size={15} /></IconButton>
                </div>
              </td>
            </tr>
          ))}
          {rows.length === 0 && <EmptyRow colSpan={6} label="No users found." />}
        </TableShell>
      )}
      <Pager page={page} count={count} pageSize={pageSize} onPage={setPage} onPageSize={(n) => { setPageSize(n); setPage(1); }} />

      <Modal open={modalOpen} title={form.id ? "Edit user" : "Add user"} subtitle={form.id ? form.email : "Create a new account"} onClose={() => setModalOpen(false)}>
        <div className="space-y-3">
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={form.email} disabled={!!form.id} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="user@example.com" />
          </div>
          <div><label className="label">Full name</label><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div>
            <label className="label">Role</label>
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}>
              <option value="candidate">Candidate</option>
              <option value="employer">Employer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label className="label">{form.id ? "New password (leave blank to keep)" : "Password (optional — random if blank)"}</label>
            <input className="input" type="text" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="••••••••" />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Active
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={() => setModalOpen(false)} className="btn-outline !py-2 !text-sm">Cancel</button>
            <button onClick={save} disabled={saving || (!form.id && !form.email)} className="btn-primary !py-2 !text-sm">{saving ? <Spinner size={15} /> : "Save"}</button>
          </div>
        </div>
      </Modal>
    </>
  );
}
