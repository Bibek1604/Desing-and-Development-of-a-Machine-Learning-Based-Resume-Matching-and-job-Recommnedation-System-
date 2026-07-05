"use client";

import { useState, useEffect, useRef, useCallback, type FormEvent } from "react";
import {
  Briefcase, Users, CheckCircle, MapPin, AlertTriangle, ChevronDown,
  Building2, Plus, Eye, EyeOff, Pause, Play, Save, Camera, Inbox, Clock,
} from "lucide-react";
import { useRequireAuth } from "@/context/AuthContext";
import {
  jobs as jobsApi, matching, employerProfile, applications as applicationsApi, mediaUrl, humanizeError,
  type Job, type CandidateMatch, type EmployerProfile, type CandidateResume, type Application,
} from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import Spinner from "@/components/Spinner";
import ErrorState from "@/components/ErrorState";
import ErrorBoundary from "@/components/ErrorBoundary";
import CompanyLogo from "@/components/CompanyLogo";
import Avatar from "@/components/Avatar";
import { scoreBadgeClass } from "@/lib/score";

const JOB_TYPES = [
  { value: "full_time",  label: "Full Time" },
  { value: "part_time",  label: "Part Time" },
  { value: "internship", label: "Internship" },
  { value: "contract",   label: "Contract" },
  { value: "remote",     label: "Remote" },
];

/** Unwrap a DRF response that may be a bare array or { results: [] }. */
function asList<T>(r: T[] | { results: T[] }): T[] {
  return Array.isArray(r) ? r : (r?.results ?? []);
}

function Field({ label, required, children }: {
  label: string; required?: boolean; children: React.ReactNode;
}) {
  return (
    <div>
      <label className="label">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Post a Job
// ─────────────────────────────────────────────────────────────────────────────
function PostJobForm({ initialCompany, initialJob, mode = "create", onPosted, onCancel }: {
  initialCompany?: string;
  initialJob?: Job;                  // supplied in edit mode
  mode?: "create" | "edit";          // create posts a new job, edit PATCHes an existing one
  onPosted: (job: Job) => void;
  onCancel?: () => void;             // shown as a "Cancel" button in edit mode
}) {
  const isEdit = mode === "edit" && initialJob != null;
  const toast = useToast();
  const [title,        setTitle]        = useState(initialJob?.title ?? "");
  const [company,      setCompany]      = useState(initialJob?.company ?? initialCompany ?? "");
  const [location,     setLocation]     = useState(initialJob?.location ?? "Kathmandu, Nepal");
  const [jobType,      setJobType]      = useState(initialJob?.job_type ?? "full_time");
  const [description,  setDescription]  = useState(initialJob?.description ?? "");
  const [requirements, setRequirements] = useState(initialJob?.requirements ?? "");
  const [salaryMin,    setSalaryMin]    = useState(initialJob?.salary_min ? String(initialJob.salary_min) : "");
  const [salaryMax,    setSalaryMax]    = useState(initialJob?.salary_max ? String(initialJob.salary_max) : "");
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState("");

  // Keep company in sync once the profile loads (only if untouched).
  useEffect(() => {
    if (!isEdit && initialCompany) setCompany(prev => prev || initialCompany);
  }, [initialCompany, isEdit]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        title, company, location,
        job_type: jobType,
        description, requirements,
        salary_min: salaryMin ? Number(salaryMin) : undefined,
        salary_max: salaryMax ? Number(salaryMax) : undefined,
      };
      const job = isEdit
        ? await jobsApi.update(initialJob!.id, payload)
        : await jobsApi.create(payload);
      onPosted(job);
      toast.success(isEdit ? "Job updated" : "Job posted successfully!");
    } catch (err) {
      const msg = humanizeError(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card p-6 sm:p-7 space-y-5">
      <div>
        <h2 className="subheading">Post a New Job</h2>
        <p className="text-sm text-slate-500 mt-0.5">
          Our AI will instantly rank the best-matched candidates after posting.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-lg border border-red-200/70 bg-red-50 p-3.5 text-sm text-red-700" role="alert">
          <AlertTriangle size={15} className="mt-0.5 shrink-0 text-red-500" />
          {error}
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Job Title" required>
          <input
            type="text" required value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Backend Developer"
            className="input"
          />
        </Field>
        <Field label="Company" required>
          <input
            type="text" required value={company}
            onChange={e => setCompany(e.target.value)}
            placeholder="e.g. Leapfrog Technology"
            className="input"
          />
        </Field>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Location">
          <input
            type="text" value={location}
            onChange={e => setLocation(e.target.value)}
            className="input"
          />
        </Field>
        <Field label="Job Type">
          <div className="relative">
            <select
              value={jobType}
              onChange={e => setJobType(e.target.value)}
              className="input appearance-none pr-9 cursor-pointer"
            >
              {JOB_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </Field>
      </div>

      <Field label="Description" required>
        <textarea
          required rows={4} value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Describe the role, responsibilities, and ideal candidate&hellip;"
          className="input resize-none"
        />
      </Field>

      <Field label="Requirements">
        <textarea
          rows={3} value={requirements}
          onChange={e => setRequirements(e.target.value)}
          placeholder="List required skills, experience, and qualifications&hellip;"
          className="input resize-none"
        />
      </Field>

      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Min Salary (NPR / month)">
          <input
            type="number" value={salaryMin}
            onChange={e => setSalaryMin(e.target.value)}
            placeholder="e.g. 40000"
            className="input"
          />
        </Field>
        <Field label="Max Salary (NPR / month)">
          <input
            type="number" value={salaryMax}
            onChange={e => setSalaryMax(e.target.value)}
            placeholder="e.g. 80000"
            className="input"
          />
        </Field>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="btn-primary w-full justify-center !py-3 !text-md"
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <Spinner size={16} />
            Posting &amp; matching&hellip;
          </span>
        ) : (
          <>
            <Briefcase size={16} />
            Post Job &amp; Find Candidates
          </>
        )}
      </button>
    </form>
  );
}

function CandidateCard({ match, rank, onViewResume }: {
  match: CandidateMatch; rank: number; onViewResume?: () => void;
}) {
  const score = match.score ?? 0;

  const initials = (match.candidate?.full_name ?? "??")
    .split(" ").slice(0, 2).map((n: string) => n[0]).join("").toUpperCase();

  const skills = match.matched_skills ?? [];

  return (
    <div className="flex items-center gap-4 rounded-lg border border-slate-200/80 bg-white p-4 transition-all duration-150 hover:border-slate-300 hover:shadow-card">
      <span className="text-sm font-bold tabular-nums text-slate-300 w-5 shrink-0 text-right">{rank}</span>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-white text-sm font-bold">
        {initials}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-slate-900 truncate text-sm">
          {match.candidate?.full_name ?? "Candidate"}
        </p>
        <p className="text-xs text-slate-500 truncate">
          {match.candidate?.degree ?? ""}
          {match.candidate?.university ? ` · ${match.candidate.university}` : ""}
        </p>
        {skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {skills.slice(0, 4).map((s: string, i: number) => (
              <span key={i} className="chip text-2xs">{s}</span>
            ))}
            {skills.length > 4 && (
              <span className="text-2xs font-medium text-slate-400 self-center">
                +{skills.length - 4} more
              </span>
            )}
          </div>
        )}
      </div>
      <div className="text-right shrink-0 space-y-1.5">
        <span className={scoreBadgeClass(score)}>{score}%</span>
        {match.candidate?.cgpa && (
          <p className="text-2xs text-slate-500 tabular-nums">CGPA {match.candidate.cgpa}</p>
        )}
        {onViewResume && (
          <button
            onClick={onViewResume}
            className="block ml-auto text-2xs font-semibold text-brand-600 hover:text-brand-700 transition-colors"
          >
            View CV
          </button>
        )}
      </div>
    </div>
  );
}

function ResumeDrawer({ userId, name, onClose }: {
  userId: number | null; name: string; onClose: () => void;
}) {
  const [data, setData] = useState<CandidateResume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) return;
    setLoading(true); setError(""); setData(null);
    matching.candidateResume(userId)
      .then(setData)
      .catch(err => setError(humanizeError(err)))
      .finally(() => setLoading(false));
  }, [userId]);

  if (!userId) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative z-50 w-full max-w-lg bg-white h-full flex flex-col overflow-hidden shadow-pop animate-slide-in-right">
        <div className="shrink-0 bg-white/95 backdrop-blur border-b border-slate-100 px-6 py-4 flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold tracking-[-0.01em] text-slate-900 truncate">{name || "Candidate"}</h2>
            <p className="text-xs text-slate-500">Resume</p>
          </div>
          <button onClick={onClose} aria-label="Close" className="shrink-0 flex h-8 w-8 items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">✕</button>
        </div>
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 min-w-0">
          {loading ? (
            <div className="space-y-3">{[...Array(6)].map((_, i) => <div key={i} className="skeleton h-5" />)}</div>
          ) : error ? (
            <p className="text-sm text-red-600">{error}</p>
          ) : data ? (
            <div className="space-y-4 min-w-0">
              <div className="text-sm text-slate-600">
                {data.degree}{data.university ? ` · ${data.university}` : ""}
              </div>
              {data.skills.length > 0 && (
                <div className="flex flex-wrap gap-1.5 w-full">
                  {data.skills.map((s, i) => <span key={i} className="chip text-2xs">{s}</span>)}
                </div>
              )}
              {data.file_url && (
                <a href={mediaUrl(data.file_url) ?? "#"} target="_blank" rel="noopener noreferrer"
                  className="btn-outline !py-2 !text-xs !px-4 inline-flex">Download original file</a>
              )}
              <div className="min-w-0">
                <p className="text-xs font-bold uppercase tracking-[0.06em] text-slate-500 mb-2">Resume text</p>
                <pre className="whitespace-pre-wrap break-words w-full rounded-lg bg-slate-50 p-4 text-xs leading-relaxed text-slate-700 max-h-[60vh] overflow-y-auto overflow-x-hidden font-sans">
                  {data.raw_text || "No parsed text available."}
                </pre>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/** Ranked-candidates panel, reused by Post and My Postings. */
function CandidatesPanel({ jobId }: { jobId: number }) {
  const [candidates,  setCandidates]  = useState<CandidateMatch[]>([]);
  const [candLoading, setCandLoading] = useState(false);
  const [candError,   setCandError]   = useState<unknown>(null);
  const [resumeCand,  setResumeCand]  = useState<{ id: number; name: string } | null>(null);

  const loadCandidates = useCallback(() => {
    setCandLoading(true);
    setCandError(null);
    matching.jobCandidates(jobId)
      .then(r => setCandidates((r as { results: CandidateMatch[] }).results ?? r))
      .catch((err) => { setCandError(err); setCandidates([]); })
      .finally(() => setCandLoading(false));
  }, [jobId]);

  useEffect(() => { loadCandidates(); }, [loadCandidates]);

  return (
    <ErrorBoundary label="candidate matches">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Users size={15} />
              </span>
              <h2 className="subheading">Ranked Candidates</h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {candLoading ? "Matching in progress…" : `${candidates.length} candidates found`}
            </p>
          </div>
        </div>

        {candLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton h-20" />
            ))}
          </div>
        ) : candError ? (
          <ErrorState
            variant="error"
            title="Couldn't load candidates"
            message={humanizeError(candError)}
            onRetry={loadCandidates}
          />
        ) : candidates.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3 ring-1 ring-slate-200/70">
              <Users size={22} className="text-slate-400" />
            </div>
            <p className="text-sm text-slate-500">No matching candidates yet</p>
            <p className="text-xs text-slate-500 mt-1">Candidates will appear as they upload CVs matching this role</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {candidates.map((c, i) => (
              <CandidateCard
                key={c.candidate?.id ?? i}
                match={c}
                rank={i + 1}
                onViewResume={c.candidate?.id ? () => setResumeCand({ id: c.candidate!.id, name: c.candidate?.full_name ?? "Candidate" }) : undefined}
              />
            ))}
          </div>
        )}
      </div>
      <ResumeDrawer
        userId={resumeCand?.id ?? null}
        name={resumeCand?.name ?? ""}
        onClose={() => setResumeCand(null)}
      />
    </ErrorBoundary>
  );
}

function PostJobPanel({ initialCompany }: { initialCompany?: string }) {
  const [postedJob, setPostedJob] = useState<Job | null>(null);

  if (!postedJob) {
    return <PostJobForm initialCompany={initialCompany} onPosted={setPostedJob} />;
  }

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="card !border-emerald-200/70 !bg-emerald-50/70 p-5 flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100">
          <CheckCircle size={20} className="text-emerald-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-emerald-900 truncate">
            &ldquo;{postedJob.title}&rdquo; posted successfully
          </p>
          <div className="flex items-center gap-1.5 mt-0.5 text-sm text-emerald-700">
            <span>{postedJob.company}</span>
            <span>&middot;</span>
            <MapPin size={12} />
            <span>{postedJob.location}</span>
          </div>
        </div>
        <button
          onClick={() => setPostedJob(null)}
          className="shrink-0 text-xs font-semibold text-emerald-700 hover:text-emerald-900 transition-colors duration-150 underline underline-offset-2"
        >
          Post another
        </button>
      </div>

      <CandidatesPanel jobId={postedJob.id} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// My Postings
// ─────────────────────────────────────────────────────────────────────────────
function PostingRow({ job, onChanged }: { job: Job; onChanged: () => void }) {
  const toast = useToast();
  const [open, setOpen]       = useState(false);
  const [busy, setBusy]       = useState(false);
  const [active, setActive]   = useState(job.is_active);

  async function toggleActive() {
    setBusy(true);
    try {
      await jobsApi.update(job.id, { is_active: !active });
      setActive(!active);
      toast.success(!active ? "Job reopened" : "Job closed");
      onChanged();
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setBusy(false);
    }
  }

  const typeLabel = JOB_TYPES.find(t => t.value === job.job_type)?.label ?? job.job_type;

  return (
    <div className="rounded-lg border border-slate-200/80 bg-white">
      <div className="flex items-center gap-4 p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-brand-100">
          <Briefcase size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-semibold text-slate-900 truncate text-sm">{job.title}</p>
            <span className={active ? "chip-green text-2xs" : "chip-slate text-2xs"}>
              {active ? "Active" : "Closed"}
            </span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">
            {typeLabel}
            {job.location ? ` · ${job.location}` : ""}
            {job.created_at ? ` · posted ${new Date(job.created_at).toLocaleDateString()}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setOpen(o => !o)}
            className="btn-outline !px-3 !py-2 !text-xs"
          >
            {open ? <EyeOff size={14} /> : <Eye size={14} />}
            {open ? "Hide" : "Candidates"}
          </button>
          <button
            onClick={toggleActive}
            disabled={busy}
            className="btn-ghost !px-3 !py-2 !text-xs"
            title={active ? "Close this posting" : "Reopen this posting"}
          >
            {busy ? <Spinner size={14} /> : active ? <Pause size={14} /> : <Play size={14} />}
            {active ? "Close" : "Reopen"}
          </button>
        </div>
      </div>
      {open && (
        <div className="border-t border-slate-100 p-4">
          <CandidatesPanel jobId={job.id} />
        </div>
      )}
    </div>
  );
}

function MyPostingsPanel() {
  const [list,    setList]    = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    jobsApi.mine()
      .then(r => setList(asList(r)))
      .catch(err => { setError(err); setList([]); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-20" />)}
      </div>
    );
  }
  if (error) {
    return (
      <ErrorState
        variant="error"
        title="Couldn't load your postings"
        message={humanizeError(error)}
        onRetry={load}
      />
    );
  }
  if (list.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center py-14 text-center">
        <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3 ring-1 ring-slate-200/70">
          <Briefcase size={22} className="text-slate-400" />
        </div>
        <p className="text-sm text-slate-600 font-medium">No job postings yet</p>
        <p className="text-xs text-slate-500 mt-1">Use the “Post a Job” tab to publish your first role.</p>
      </div>
    );
  }

  const activeCount = list.filter(j => j.is_active).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          {list.length} posting{list.length === 1 ? "" : "s"} · {activeCount} active
        </p>
        <button onClick={load} className="text-xs font-semibold text-brand-600 hover:text-brand-700">
          Refresh
        </button>
      </div>
      <div className="space-y-3">
        {list.map(job => (
          <PostingRow key={job.id} job={job} onChanged={load} />
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Company Profile
// ─────────────────────────────────────────────────────────────────────────────
function CompanyProfilePanel({ onSaved }: { onSaved?: (p: EmployerProfile) => void }) {
  const toast = useToast();
  const [form,    setForm]    = useState<EmployerProfile>({
    company_name: "", website: "", location: "", description: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);
  const [error,   setError]   = useState<unknown>(null);
  const [logo,    setLogo]    = useState<string>("");
  const [logoBusy, setLogoBusy] = useState(false);
  const logoRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    employerProfile.get()
      .then(p => {
        setForm({
          company_name: p.company_name ?? "",
          website:      p.website ?? "",
          location:     p.location ?? "",
          description:  p.description ?? "",
        });
        setLogo(p.logo ?? "");
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleLogo(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) { toast.error("Please choose an image file."); return; }
    setLogoBusy(true);
    try {
      const r = await employerProfile.uploadLogo(file);
      setLogo(r.logo);
      toast.success("Company logo updated.");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setLogoBusy(false);
      if (logoRef.current) logoRef.current.value = "";
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const saved = await employerProfile.update(form);
      toast.success("Company profile saved");
      onSaved?.(saved);
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="card p-6 sm:p-7 space-y-4">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-12" />)}
      </div>
    );
  }
  if (error) {
    return (
      <ErrorState
        variant="error"
        title="Couldn't load company profile"
        message={humanizeError(error)}
        onRetry={load}
      />
    );
  }

  return (
    <form onSubmit={handleSubmit} className="card p-6 sm:p-7 space-y-5">
      <div className="flex items-center gap-4">
        <div className="relative shrink-0">
          <CompanyLogo name={form.company_name || "Company"} src={logo} size={64} />
          <input ref={logoRef} type="file" accept="image/*" onChange={handleLogo} className="hidden" />
          <button
            type="button"
            onClick={() => logoRef.current?.click()}
            disabled={logoBusy}
            aria-label="Upload company logo"
            className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white shadow-sm ring-2 ring-white hover:bg-brand-700 transition-colors disabled:opacity-60"
          >
            {logoBusy ? <Spinner size={12} /> : <Camera size={13} />}
          </button>
        </div>
        <div>
          <h2 className="subheading">Company Profile</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Set once — your company name &amp; logo appear on every job you post.
          </p>
        </div>
      </div>

      <Field label="Company Name" required>
        <input
          type="text" required value={form.company_name}
          onChange={e => setForm({ ...form, company_name: e.target.value })}
          placeholder="e.g. Leapfrog Technology"
          className="input"
        />
      </Field>

      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Website">
          <input
            type="url" value={form.website}
            onChange={e => setForm({ ...form, website: e.target.value })}
            placeholder="https://yourcompany.com"
            className="input"
          />
        </Field>
        <Field label="Location">
          <input
            type="text" value={form.location}
            onChange={e => setForm({ ...form, location: e.target.value })}
            placeholder="Kathmandu, Nepal"
            className="input"
          />
        </Field>
      </div>

      <Field label="About the Company">
        <textarea
          rows={4} value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
          placeholder="What your company does, culture, and mission&hellip;"
          className="input resize-none"
        />
      </Field>

      <button type="submit" disabled={saving} className="btn-primary justify-center !py-3 !text-md">
        {saving ? (
          <span className="flex items-center gap-2"><Spinner size={16} /> Saving&hellip;</span>
        ) : (
          <><Save size={16} /> Save Company Profile</>
        )}
      </button>
    </form>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Applicants (people who actually applied to my jobs)
// ─────────────────────────────────────────────────────────────────────────────
const APP_STATUS: { value: Application["status"]; label: string }[] = [
  { value: "applied",     label: "Applied" },
  { value: "reviewed",    label: "Reviewed" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "rejected",    label: "Rejected" },
];

function ApplicantsPanel() {
  const toast = useToast();
  const [apps,    setApps]    = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<unknown>(null);
  const [busyId,  setBusyId]  = useState<number | null>(null);
  const [resumeCand, setResumeCand] = useState<{ id: number; name: string } | null>(null);

  const load = useCallback(() => {
    setLoading(true); setError(null);
    applicationsApi.list()
      .then(r => setApps(Array.isArray(r) ? r : r.results ?? []))
      .catch(err => { setError(err); setApps([]); })
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { load(); }, [load]);

  async function setStatus(id: number, status: Application["status"]) {
    setBusyId(id);
    try {
      await applicationsApi.updateStatus(id, status);
      setApps(prev => prev.map(a => (a.id === id ? { ...a, status } : a)));
      toast.success("Applicant status updated.");
    } catch (err) {
      toast.error(humanizeError(err));
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="skeleton h-24" />)}</div>;
  }
  if (error) {
    return <ErrorState variant="error" title="Couldn't load applicants" message={humanizeError(error)} onRetry={load} />;
  }
  if (apps.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center py-16 text-center">
        <div className="h-12 w-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3 ring-1 ring-slate-200/70">
          <Inbox size={22} className="text-slate-400" />
        </div>
        <p className="font-medium text-slate-600">No applicants yet</p>
        <p className="text-sm text-slate-500 mt-1">When candidates apply to your jobs, they&apos;ll appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">{apps.length} applicant{apps.length === 1 ? "" : "s"} across your jobs</p>
      {apps.map(a => {
        const c = a.candidate_detail;
        return (
          <div key={a.id} className="card p-4 flex flex-wrap items-center gap-4">
            <Avatar name={c?.full_name} src={c?.avatar ?? null} size={44} />
            <div className="flex-1 min-w-[12rem]">
              <p className="font-semibold text-slate-900 text-sm truncate">{c?.full_name ?? "Candidate"}</p>
              <p className="text-xs text-slate-500 truncate">
                Applied to <span className="font-medium text-slate-600">{a.job_detail?.title ?? `Job #${a.job}`}</span>
                {c?.university ? ` · ${c.university}` : ""}
              </p>
              <p className="text-2xs text-slate-400 mt-0.5 inline-flex items-center gap-1">
                <Clock size={10} /> {new Date(a.applied_at).toLocaleDateString()}
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {a.match_score > 0 && <span className={scoreBadgeClass(a.match_score)}>{a.match_score}%</span>}
              <div className="relative">
                <select
                  value={a.status}
                  disabled={busyId === a.id}
                  onChange={e => setStatus(a.id, e.target.value as Application["status"])}
                  className="input !py-1.5 !text-xs appearance-none pr-7 cursor-pointer"
                >
                  {APP_STATUS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
                <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              </div>
              {c?.id && (
                <button onClick={() => setResumeCand({ id: c.id, name: c.full_name })} className="btn-outline !py-1.5 !px-3 !text-xs">
                  <Eye size={13} /> CV
                </button>
              )}
            </div>
          </div>
        );
      })}
      <ResumeDrawer userId={resumeCand?.id ?? null} name={resumeCand?.name ?? ""} onClose={() => setResumeCand(null)} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────
type Tab = "post" | "postings" | "applicants" | "company";

const TABS: { id: Tab; label: string; icon: typeof Briefcase }[] = [
  { id: "post",       label: "Post a Job",  icon: Plus },
  { id: "postings",   label: "My Postings", icon: Briefcase },
  { id: "applicants", label: "Applicants",  icon: Inbox },
  { id: "company",    label: "Company",     icon: Building2 },
];

export default function EmployerPage() {
  // Role-gate: only employer accounts may open the job-uploader section.
  const { isLoading, user } = useRequireAuth("/login", "employer");

  const [tab, setTab] = useState<Tab>("post");
  const [company, setCompany] = useState<string>("");

  // Prefill the post form with the saved company name.
  useEffect(() => {
    if (isLoading || user?.role !== "employer") return;
    employerProfile.get()
      .then(p => setCompany(p.company_name ?? ""))
      .catch(() => {});
  }, [isLoading, user]);

  if (isLoading || user?.role !== "employer") {
    return (
      <div className="page flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-brand-600 border-t-transparent animate-spin" role="status" aria-label="Loading" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-inner-sm">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2.5 mb-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-brand-100">
              <Briefcase size={18} />
            </span>
            <h1 className="page-title">Employer Portal</h1>
          </div>
          <p className="muted">
            Post a job and our AI instantly ranks the best-matched candidates from Nepal&apos;s talent pool.
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6 grid grid-cols-2 sm:grid-cols-4 gap-1.5 rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setTab(id)}
              aria-pressed={tab === id}
              className={`flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-all duration-150 ${
                tab === id
                  ? "bg-brand-600 text-white shadow-sm"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>

        {tab === "post"       && <PostJobPanel initialCompany={company} />}
        {tab === "postings"   && <MyPostingsPanel />}
        {tab === "applicants" && <ApplicantsPanel />}
        {tab === "company"    && <CompanyProfilePanel onSaved={(p) => setCompany(p.company_name)} />}
      </div>
    </div>
  );
}
