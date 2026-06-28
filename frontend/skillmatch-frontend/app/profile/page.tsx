"use client";

import { useState, useEffect, useRef, type FormEvent } from "react";
import {
  User, GraduationCap, Target, Link2, Save, ChevronDown,
  Sparkles, Upload, FileText, Trash2, AlertTriangle, Camera,
} from "lucide-react";
import { useRequireAuth, useAuth } from "@/context/AuthContext";
import { candidateProfile, resumes as resumesApi, auth as authApi, mediaUrl, humanizeError, type CandidateProfileData } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import Spinner from "@/components/Spinner";
import ErrorState from "@/components/ErrorState";
import Avatar from "@/components/Avatar";

const AVAILABILITY = [
  { value: "",           label: "Select availability" },
  { value: "immediate",  label: "Immediate" },
  { value: "2_weeks",    label: "Within 2 weeks" },
  { value: "1_month",    label: "Within 1 month" },
  { value: "3_months",   label: "Within 3 months" },
  { value: "6_months",   label: "Within 6 months" },
];

function Field({ label, children, hint }: {
  label: string; children: React.ReactNode; hint?: string;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}

function SectionCard({ icon: Icon, title, subtitle, children }: {
  icon: React.ElementType; title: string; subtitle?: string; children: React.ReactNode;
}) {
  return (
    <div className="card p-6 sm:p-7 space-y-5">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-brand-100">
          <Icon size={17} />
        </span>
        <div>
          <h2 className="subheading">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {children}
    </div>
  );
}

const EMPTY: CandidateProfileData = {
  headline: "", phone: "", location: "", district: "", province: "",
  degree: "", college: "", university: "", graduation_year: null, cgpa: "",
  preferred_role: "", expected_salary_min: null, expected_salary_max: null,
  availability: "", industry_interest: "", career_objective: "", resume_summary: "",
  github_url: "", linkedin_url: "", portfolio_url: "",
};

export default function ProfilePage() {
  const { isLoading, user } = useRequireAuth("/login", "candidate");
  const { logout } = useAuth();
  const toast = useToast();

  const [form,    setForm]    = useState<CandidateProfileData>(EMPTY);
  const [skills,  setSkills]  = useState<Array<{ id: number; name: string }>>([]);
  const [atsScore, setAtsScore] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);
  const [uploading, setUploading] = useState(false);
  const [consent, setConsent] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [avatar, setAvatar] = useState<string>("");
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [resumeFile, setResumeFile] = useState<string>("");
  const [resumeName, setResumeName] = useState<string>("");
  const [error,   setError]   = useState<unknown>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const avatarRef = useRef<HTMLInputElement>(null);

  async function handleAvatar(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) { toast.error("Please choose an image file."); return; }
    setAvatarBusy(true);
    try {
      const r = await candidateProfile.uploadAvatar(file);
      setAvatar(r.avatar);
      toast.success("Profile photo updated.");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setAvatarBusy(false);
      if (avatarRef.current) avatarRef.current.value = "";
    }
  }

  async function handleDeleteAccount() {
    if (!window.confirm("Permanently delete your account and all your data? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await authApi.deleteAccount();
      toast.success("Your account has been deleted.");
      logout();
      window.location.assign("/");
    } catch (err) {
      toast.error(humanizeError(err));
      setDeleting(false);
    }
  }

  function applyProfile(p: CandidateProfileData) {
    setForm({
      headline: p.headline ?? "", phone: p.phone ?? "", location: p.location ?? "",
      district: p.district ?? "", province: p.province ?? "",
      degree: p.degree ?? "", college: p.college ?? "", university: p.university ?? "",
      graduation_year: p.graduation_year ?? null, cgpa: p.cgpa ?? "",
      preferred_role: p.preferred_role ?? "",
      expected_salary_min: p.expected_salary_min ?? null,
      expected_salary_max: p.expected_salary_max ?? null,
      availability: p.availability ?? "", industry_interest: p.industry_interest ?? "",
      career_objective: p.career_objective ?? "", resume_summary: p.resume_summary ?? "",
      github_url: p.github_url ?? "", linkedin_url: p.linkedin_url ?? "",
      portfolio_url: p.portfolio_url ?? "",
    });
    setSkills(p.skills ?? []);
    setAtsScore(p.ats_score ?? 0);
    setAvatar(p.avatar ?? "");
  }

  useEffect(() => {
    if (isLoading || user?.role !== "candidate") return;
    candidateProfile.get()
      .then(applyProfile)
      .catch(setError)
      .finally(() => setLoading(false));
    // Also load the candidate's uploaded resume file so they can view it.
    resumesApi.list()
      .then(r => {
        const list = Array.isArray(r) ? r : r.results ?? [];
        const primary = list.find(x => x.is_primary) ?? list[0];
        if (primary?.file) { setResumeFile(primary.file); setResumeName(primary.original_filename ?? "resume"); }
      })
      .catch(() => {});
  }, [isLoading, user]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const okExt = /\.(pdf|docx?|txt)$/i.test(file.name);
    if (!okExt) { toast.error("Upload a PDF, DOCX, or TXT file."); return; }
    setUploading(true);
    try {
      const up = await resumesApi.upload(file, true);
      if (up?.file) { setResumeFile(up.file); setResumeName(up.original_filename ?? file.name); }
      // The backend parses the resume and fills in skills, education, links and
      // bio — re-fetch so the form reflects everything it extracted.
      const fresh = await candidateProfile.get();
      applyProfile(fresh);
      toast.success("Resume uploaded — we filled in what we could from it.");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function set<K extends keyof CandidateProfileData>(key: K, value: CandidateProfileData[K]) {
    setForm(prev => ({ ...prev, [key]: value }));
  }
  const num = (v: string) => (v === "" ? null : Number(v));

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await candidateProfile.update(form);
      toast.success("Profile saved — your matches will refresh.");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setSaving(false);
    }
  }

  if (isLoading || user?.role !== "candidate" || loading) {
    return (
      <div className="page">
        <div className="page-inner-sm space-y-5">
          <div className="skeleton h-24" />
          <div className="skeleton h-64" />
          <div className="skeleton h-64" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="page-inner-sm">
          <ErrorState
            variant="error"
            title="Couldn't load your profile"
            message={humanizeError(error)}
            onRetry={() => location.reload()}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-inner-sm">

        {/* Header */}
        <div className="mb-7 flex items-center gap-4">
          <div className="relative shrink-0">
            <Avatar name={user?.full_name} src={avatar} size={72} />
            <input ref={avatarRef} type="file" accept="image/*" onChange={handleAvatar} className="hidden" />
            <button
              type="button"
              onClick={() => avatarRef.current?.click()}
              disabled={avatarBusy}
              aria-label="Change profile photo"
              className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white shadow-sm ring-2 ring-white hover:bg-brand-700 transition-colors disabled:opacity-60"
            >
              {avatarBusy ? <Spinner size={12} /> : <Camera size={13} />}
            </button>
          </div>
          <div className="min-w-0">
            <h1 className="page-title">My Profile</h1>
            <p className="muted">
              Keep your details and preferences up to date — the AI uses them to match you to the right jobs.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">

          {/* Resume upload + auto-extracted data */}
          <div className="card p-6 space-y-4">
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleUpload}
              className="hidden"
            />
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-brand-100">
                  <FileText size={17} />
                </span>
                <div className="min-w-0">
                  <h2 className="subheading">Your Resume</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Upload your CV — we auto-fill your skills, education, links and bio from it.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4 shrink-0">
                {atsScore > 0 && (
                  <div className="text-center">
                    <p className="text-2xl font-bold text-brand-600 tabular-nums">{atsScore}</p>
                    <p className="text-2xs text-slate-500">ATS score</p>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  disabled={uploading || !consent}
                  className="btn-primary !py-2.5 !text-sm !px-4"
                  title={!consent ? "Please accept the consent below to upload" : undefined}
                >
                  {uploading
                    ? <span className="flex items-center gap-2"><Spinner size={14} /> Parsing…</span>
                    : <><Upload size={14} /> {skills.length ? "Replace CV" : "Upload CV"}</>}
                </button>
              </div>
            </div>

            {/* Consent (GDPR) — required before uploading */}
            <label className="flex items-start gap-2.5 rounded-lg bg-slate-50 p-3 text-xs text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={consent}
                onChange={e => setConsent(e.target.checked)}
                className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              <span>
                I consent to SkillMatch processing my resume to extract skills and match me to jobs, as described
                in the <a href="/privacy" className="font-semibold text-brand-600 hover:text-brand-700">Privacy Policy</a>.
              </span>
            </label>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={14} className="text-brand-600" />
                <h3 className="text-xs font-bold uppercase tracking-[0.06em] text-slate-600">Skills from your resume</h3>
              </div>
              {skills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {skills.map(s => <span key={s.id} className="chip text-2xs">{s.name}</span>)}
                </div>
              ) : (
                <p className="text-xs text-slate-500">No skills yet — upload your CV to extract them automatically.</p>
              )}
            </div>

            {resumeFile && (
              <a
                href={mediaUrl(resumeFile) ?? "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors"
              >
                <FileText size={13} /> View uploaded CV{resumeName ? ` · ${resumeName}` : ""}
              </a>
            )}
          </div>

          {/* Basic details */}
          <SectionCard icon={User} title="Basic Details" subtitle="Who you are and where you're based">
            <Field label="Professional headline">
              <input className="input" value={form.headline ?? ""}
                onChange={e => set("headline", e.target.value)}
                placeholder="e.g. Junior Backend Developer | Python · Django" />
            </Field>
            <Field label="Bio / summary" hint="Auto-filled from your resume — edit anytime.">
              <textarea className="input resize-none" rows={3} value={form.resume_summary ?? ""}
                onChange={e => set("resume_summary", e.target.value)}
                placeholder="A short summary of who you are professionally…" />
            </Field>
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="Phone">
                <input className="input" value={form.phone ?? ""}
                  onChange={e => set("phone", e.target.value)} placeholder="+977 98XXXXXXXX" />
              </Field>
              <Field label="Location">
                <input className="input" value={form.location ?? ""}
                  onChange={e => set("location", e.target.value)} placeholder="Kathmandu, Nepal" />
              </Field>
              <Field label="District">
                <input className="input" value={form.district ?? ""}
                  onChange={e => set("district", e.target.value)} placeholder="Kathmandu" />
              </Field>
              <Field label="Province">
                <input className="input" value={form.province ?? ""}
                  onChange={e => set("province", e.target.value)} placeholder="Bagmati" />
              </Field>
            </div>
          </SectionCard>

          {/* Education */}
          <SectionCard icon={GraduationCap} title="Education">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="Degree">
                <input className="input" value={form.degree ?? ""}
                  onChange={e => set("degree", e.target.value)} placeholder="BSc (Hons) Computing" />
              </Field>
              <Field label="University">
                <input className="input" value={form.university ?? ""}
                  onChange={e => set("university", e.target.value)} placeholder="Coventry University" />
              </Field>
              <Field label="College">
                <input className="input" value={form.college ?? ""}
                  onChange={e => set("college", e.target.value)} placeholder="Softwarica College" />
              </Field>
              <Field label="Graduation year">
                <input className="input" type="number" value={form.graduation_year ?? ""}
                  onChange={e => set("graduation_year", num(e.target.value))} placeholder="2026" />
              </Field>
              <Field label="CGPA">
                <input className="input" type="number" step="0.01" value={(form.cgpa as string) ?? ""}
                  onChange={e => set("cgpa", e.target.value)} placeholder="3.50" />
              </Field>
            </div>
          </SectionCard>

          {/* Career preferences — needs & demands */}
          <SectionCard icon={Target} title="Job Preferences" subtitle="Your needs and demands — used to rank job matches">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="Preferred role">
                <input className="input" value={form.preferred_role ?? ""}
                  onChange={e => set("preferred_role", e.target.value)} placeholder="Backend Developer" />
              </Field>
              <Field label="Industry interest">
                <input className="input" value={form.industry_interest ?? ""}
                  onChange={e => set("industry_interest", e.target.value)} placeholder="Fintech, SaaS" />
              </Field>
              <Field label="Expected salary — min (NPR/month)">
                <input className="input" type="number" value={form.expected_salary_min ?? ""}
                  onChange={e => set("expected_salary_min", num(e.target.value))} placeholder="40000" />
              </Field>
              <Field label="Expected salary — max (NPR/month)">
                <input className="input" type="number" value={form.expected_salary_max ?? ""}
                  onChange={e => set("expected_salary_max", num(e.target.value))} placeholder="80000" />
              </Field>
              <Field label="Availability">
                <div className="relative">
                  <select className="input appearance-none pr-9 cursor-pointer" value={form.availability ?? ""}
                    onChange={e => set("availability", e.target.value)}>
                    {AVAILABILITY.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
              </Field>
            </div>
            <Field label="Career objective">
              <textarea className="input resize-none" rows={3} value={form.career_objective ?? ""}
                onChange={e => set("career_objective", e.target.value)}
                placeholder="What you're looking for and where you want to grow…" />
            </Field>
          </SectionCard>

          {/* Links */}
          <SectionCard icon={Link2} title="Links & Portfolio">
            <div className="grid sm:grid-cols-2 gap-4">
              <Field label="GitHub">
                <input className="input" type="url" value={form.github_url ?? ""}
                  onChange={e => set("github_url", e.target.value)} placeholder="https://github.com/username" />
              </Field>
              <Field label="LinkedIn">
                <input className="input" type="url" value={form.linkedin_url ?? ""}
                  onChange={e => set("linkedin_url", e.target.value)} placeholder="https://linkedin.com/in/username" />
              </Field>
              <Field label="Portfolio">
                <input className="input" type="url" value={form.portfolio_url ?? ""}
                  onChange={e => set("portfolio_url", e.target.value)} placeholder="https://yoursite.com" />
              </Field>
            </div>
          </SectionCard>

          {/* Sticky save */}
          <div className="sticky bottom-4 flex justify-end">
            <button type="submit" disabled={saving}
              className="btn-primary !py-3 !px-7 !text-md shadow-pop">
              {saving
                ? <span className="flex items-center gap-2"><Spinner size={16} /> Saving…</span>
                : <><Save size={16} /> Save Profile</>}
            </button>
          </div>
        </form>

        {/* Danger zone — GDPR right to delete */}
        <div className="mt-8 rounded-2xl border border-red-200/70 bg-red-50/40 p-6">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={16} className="text-red-500" />
            <h2 className="text-sm font-bold text-red-700">Danger zone</h2>
          </div>
          <p className="text-xs text-slate-600 mb-4 max-w-lg">
            Permanently delete your account and all associated data — profile, resumes, and applications.
            This is immediate and cannot be undone.
          </p>
          <button
            type="button"
            onClick={handleDeleteAccount}
            disabled={deleting}
            className="inline-flex items-center gap-2 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-600 hover:text-white transition-colors disabled:opacity-50"
          >
            {deleting ? <Spinner size={14} /> : <Trash2 size={14} />}
            Delete my account
          </button>
        </div>
      </div>
    </div>
  );
}
