/**
 * Central typed API client for SkillMatch Nepal backend.
 * Base URL is read from NEXT_PUBLIC_API_URL (default: http://localhost:8000).
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Turn a relative media path (e.g. /media/avatars/x.png) into a full URL. */
export function mediaUrl(path?: string | null): string | null {
  if (!path) return null;
  return path.startsWith("http") ? path : `${BASE}${path}`;
}

// ── Token helpers ─────────────────────────────────────────────────────────────
export const tokens = {
  getAccess:  () => (typeof window !== "undefined" ? localStorage.getItem("sm_access")  : null),
  getRefresh: () => (typeof window !== "undefined" ? localStorage.getItem("sm_refresh") : null),
  set: (access: string, refresh: string) => {
    localStorage.setItem("sm_access",  access);
    localStorage.setItem("sm_refresh", refresh);
  },
  clear: () => {
    localStorage.removeItem("sm_access");
    localStorage.removeItem("sm_refresh");
  },
};

// ── Core request ──────────────────────────────────────────────────────────────
async function tryRefresh(): Promise<boolean> {
  const refresh = tokens.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE}/api/auth/refresh/`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ refresh }),
    });
    if (!res.ok) { tokens.clear(); return false; }
    const data = await res.json();
    // Honour refresh-token rotation: if the backend returns a fresh refresh
    // token (SIMPLE_JWT.ROTATE_REFRESH_TOKENS=True), use it instead of the old
    // one so stolen refresh tokens expire on next legitimate refresh.
    tokens.set(data.access, data.refresh || refresh);
    return true;
  } catch {
    tokens.clear();
    return false;
  }
}

export class APIError extends Error {
  constructor(
    public status: number,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    public data: any,
    message: string,
  ) {
    super(message);
    this.name = "APIError";
  }

  /** True when the request never reached the server (offline, CORS, DNS…). */
  get isNetworkError(): boolean {
    return this.status === 0;
  }

  /** A safe, human-readable message suitable for showing in the UI. */
  get userMessage(): string {
    return humanizeError(this);
  }
}

/**
 * Convert any thrown value into a friendly, user-facing string. Understands the
 * backend's structured error envelope ({ error: { message } }), DRF field
 * errors, network failures and timeouts.
 */
export function humanizeError(err: unknown): string {
  if (err instanceof APIError) {
    if (err.status === 0) {
      return err.message === "timeout"
        ? "The request timed out. Please check your connection and try again."
        : "We couldn't reach the server. Please check your connection and try again.";
    }
    const d = err.data as Record<string, unknown> | undefined;
    if (d && typeof d === "object") {
      const envelope = d["error"] as { message?: string } | undefined;
      if (envelope?.message) return envelope.message;
      if (typeof d["detail"] === "string") return d["detail"] as string;
      const parts: string[] = [];
      for (const [key, value] of Object.entries(d)) {
        if (Array.isArray(value)) parts.push(`${key}: ${value.join(" ")}`);
        else if (typeof value === "string") parts.push(value);
      }
      if (parts.length) return parts.join(" ");
    }
    if (err.status === 401) return "Your session has expired. Please sign in again.";
    if (err.status === 403) return "You don't have permission to do that.";
    if (err.status === 404) return "We couldn't find what you were looking for.";
    if (err.status >= 500) return "The server ran into a problem. Please try again shortly.";
    return err.message || "Something went wrong. Please try again.";
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

const DEFAULT_TIMEOUT_MS = 30_000;

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (err) {
    // AbortError => timeout; everything else from fetch() => network failure.
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new APIError(0, {}, "timeout");
    }
    throw new APIError(0, {}, "network");
  } finally {
    clearTimeout(timer);
  }
}

async function request<T>(
  path: string,
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
  body?: unknown,
  isFormData = false,
): Promise<T> {
  const headers: Record<string, string> = {};
  const access = tokens.getAccess();
  if (access) headers["Authorization"] = `Bearer ${access}`;
  if (!isFormData && body != null) headers["Content-Type"] = "application/json";

  const init: RequestInit = {
    method,
    headers,
    body: isFormData
      ? (body as FormData)
      : body != null
      ? JSON.stringify(body)
      : undefined,
  };

  let res = await fetchWithTimeout(`${BASE}${path}`, init);

  // Auto-refresh on 401
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${tokens.getAccess()!}`;
      res = await fetchWithTimeout(`${BASE}${path}`, { ...init, headers });
    } else {
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new APIError(401, {}, "Unauthorized");
    }
  }

  if (!res.ok) {
    let data: unknown;
    try { data = await res.json(); } catch { data = {}; }
    throw new APIError(res.status, data, `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export interface LoginResponse  { access: string; refresh: string }
export interface RegisterPayload {
  full_name: string;
  email:     string;
  password:  string;
  role?:     "candidate" | "employer";
}
export type UserRole = "candidate" | "employer" | "admin";

/** Landing route for each role after login/registration. */
export function homeForRole(role: UserRole | undefined): string {
  if (role === "admin") return "/admin";
  if (role === "employer") return "/employer";
  return "/dashboard";
}
export interface MeResponse {
  id:        number;
  email:     string;
  full_name: string;
  role:      UserRole;
}
export interface ProfileResponse {
  id:                 number;
  degree?:            string;
  college?:           string;
  university?:        string;
  cgpa?:              number;
  technical_skills?:  string;
  soft_skills?:       string;
  certifications?:    string;
  github_url?:        string;
  linkedin_url?:      string;
  preferred_role?:    string;
  ats_score?:         number;
  hiring_probability?:number;
}

export const auth = {
  login:  (email: string, password: string) =>
    request<LoginResponse>("/api/auth/login/", "POST", { email, password }),
  register: (payload: RegisterPayload) =>
    request<{ id: number; email: string }>("/api/auth/register/", "POST", payload),
  me:     () => request<MeResponse>("/api/auth/me/"),
  profile:() => request<ProfileResponse>("/api/auth/profile/"),
  updateProfile: (data: Partial<ProfileResponse>) =>
    request<ProfileResponse>("/api/auth/profile/", "PUT", data),
  deleteAccount: () => request<void>("/api/auth/me/delete/", "DELETE"),
};

// ── Resumes ───────────────────────────────────────────────────────────────────
export interface Resume {
  id:                number;
  file?:             string | null;
  original_filename: string;
  raw_text:          string;
  is_primary:        boolean;
  uploaded_at:       string;
  extracted_skills:  string[] | Array<{ id: number; name: string }>;
}
export interface ATSAnalysis {
  ats_score:          number;
  completeness_score: number;
  keyword_score:      number;
  formatting_score:   number;
  experience_score:   number;
  strengths:          string[];
  weaknesses:         string[];
  recommendations:    string[];
  section_scores:     Record<string, number>;
  missing_sections:   string[];
}

export const resumes = {
  list:   () => request<Resume[] | { results: Resume[]; count: number }>("/api/resumes/"),
  upload: (file: File, isPrimary = true) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("is_primary", String(isPrimary));
    return request<Resume>("/api/resumes/", "POST", fd, true);
  },
  ats:    (id: number) => request<ATSAnalysis>(`/api/resumes/${id}/ats/`),
  analyze:(text: string) =>
    request<ATSAnalysis>("/api/resumes/analyze/", "POST", { text }),
};

// ── Jobs ──────────────────────────────────────────────────────────────────────
export interface Job {
  id:          number;
  title:       string;
  company:     string;
  location:    string;
  job_type:    string;
  description: string;
  requirements:string;
  salary_min?:  number;
  salary_max?:  number;
  salary_text?: string;
  job_type_display?: string;
  company_logo?: string | null;
  required_skills?: Array<{ id: number; name: string; slug?: string; category?: string }>;
  is_active:   boolean;
  created_at:  string;
}
export interface JobCreatePayload {
  title:        string;
  company:      string;
  location?:    string;
  job_type?:    string;
  description:  string;
  requirements?:string;
  salary_min?:  number;
  salary_max?:  number;
}

export const jobs = {
  list:   (search?: string, jobType?: string, page?: number) => {
    const params = new URLSearchParams();
    if (search)  params.set("search",   search);
    if (jobType) params.set("job_type", jobType);
    if (page)    params.set("page",     String(page));
    const qs = params.toString();
    return request<Job[] | { results: Job[]; count: number; num_pages?: number; page?: number }>(
      `/api/jobs/${qs ? "?" + qs : ""}`
    );
  },
  /** The logged-in employer's own postings (active + closed). */
  mine:   () => request<Job[] | { results: Job[]; count: number }>("/api/jobs/?mine=true"),
  get:    (id: number)              => request<Job>(`/api/jobs/${id}/`),
  create: (payload: JobCreatePayload) =>
    request<Job>("/api/jobs/", "POST", payload),
  update: (id: number, payload: Partial<JobCreatePayload> & { is_active?: boolean }) =>
    request<Job>(`/api/jobs/${id}/`, "PATCH", payload),
};

// ── Employer profile ────────────────────────────────────────────────────────
export interface EmployerProfile {
  company_name: string;
  website:      string;
  location:     string;
  description:  string;
  logo?:        string;
  updated_at?:  string;
}
export const employerProfile = {
  get:    () => request<EmployerProfile>("/api/auth/profile/"),
  update: (data: Partial<EmployerProfile>) =>
    request<EmployerProfile>("/api/auth/profile/", "PUT", data),
  uploadLogo: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<{ logo: string }>("/api/auth/logo/", "POST", fd, true);
  },
};

// ── Candidate profile ────────────────────────────────────────────────────────
export interface CandidateProfileData {
  // Basic
  headline?:        string;
  phone?:           string;
  location?:        string;
  district?:        string;
  province?:        string;
  // Education
  degree?:          string;
  college?:         string;
  university?:      string;
  graduation_year?: number | null;
  cgpa?:            number | string | null;
  // Career preferences — the candidate's "needs and demands"
  preferred_role?:      string;
  expected_salary_min?: number | null;
  expected_salary_max?: number | null;
  availability?:        string;
  industry_interest?:   string;
  career_objective?:    string;
  resume_summary?:      string;
  // Extras
  soft_skills?:     string;
  certifications?:  string;
  languages?:       string;
  github_url?:      string;
  linkedin_url?:    string;
  portfolio_url?:   string;
  // Read-only (computed from resume / ML)
  avatar?:             string;
  skills?:             Array<{ id: number; name: string }>;
  resume_score?:       number;
  ats_score?:          number;
  hiring_probability?: number;
  updated_at?:         string;
}
export const candidateProfile = {
  get:    () => request<CandidateProfileData>("/api/auth/profile/"),
  update: (data: Partial<CandidateProfileData>) =>
    request<CandidateProfileData>("/api/auth/profile/", "PUT", data),
  uploadAvatar: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<{ avatar: string }>("/api/auth/avatar/", "POST", fd, true);
  },
};

// ── Matching ──────────────────────────────────────────────────────────────────
export interface JobMatch {
  job:            Job;
  score:          number;
  similarity:     number;
  matched_skills: string[];
}
export interface CandidateMatch {
  candidate:      MeResponse & { degree?: string; university?: string; cgpa?: number };
  score:          number;
  similarity:     number;
  matched_skills: string[];
}
export interface SkillGapReport {
  job_id:                 number;
  job_title:              string;
  company:                string;
  matched_skills:         string[];
  missing_skills:         string[];
  missing_technologies:   string[];
  missing_certifications: string[];
  experience_gaps:        string[];
  match_improvement_pct:  number;
}
export interface CareerRole {
  role:           string;
  confidence:     number;
  confidence_pct: number;
  reason:         string;
  missing_skills: string[];
}
export interface LearningPath {
  skill:     string;
  priority:  "high" | "medium";
  resources: string[];
  reason:    string;
}
export interface CareerRecommendations {
  recommended_roles: CareerRole[];
  learning_paths:    LearningPath[];
  top_role:          string;
}
export interface ExplainMatch {
  job_id:    number;
  job_title: string;
  score:     number;
  feature_contributions: Array<{
    feature:      string;
    value:        number;
    contribution: number;
    pct_of_score: number;
  }>;
  matched_skills:      string[];
  missing_skills:      string[];
  reasons:             string[];
  explanation_summary: string;
}
export interface DashboardData {
  profile: {
    full_name:          string;
    email:              string;
    avatar?:            string | null;
    degree:             string;
    university:         string;
    cgpa:               number | null;
    skills_count:       number;
    ats_score:          number | null;
    resume_score:       number | null;
    hiring_probability: number | null;
    preferred_role:     string;
  };
  ats_analysis:           ATSAnalysis & { strengths: string[]; weaknesses: string[]; recommendations: string[] };
  career_recommendations: CareerRecommendations;
  top_job_matches: Array<{
    job_id:         number;
    title:          string;
    company:        string;
    score:          number;
    similarity:     number;
    matched_skills: string[];
  }>;
}

export interface CandidateResume {
  user_id:    number;
  full_name:  string;
  email:      string;
  raw_text:   string;
  file_url:   string | null;
  filename:   string;
  skills:     string[];
  degree:     string;
  university: string;
}

export const matching = {
  recommendations: () =>
    request<JobMatch[]>("/api/matching/recommendations/"),
  jobCandidates: (jobId: number) =>
    request<CandidateMatch[]>(`/api/matching/jobs/${jobId}/candidates/`),
  candidateResume: (userId: number) =>
    request<CandidateResume>(`/api/matching/candidates/${userId}/resume/`),
  skillGap: (jobId: number) =>
    request<SkillGapReport>(`/api/matching/skill-gap/${jobId}/`),
  careerRecommendations: () =>
    request<CareerRecommendations>("/api/matching/career-recommendations/"),
  explain: (jobId: number) =>
    request<ExplainMatch>(`/api/matching/explain/${jobId}/`),
  dashboard: () =>
    request<DashboardData>("/api/matching/dashboard/"),
};

// ── Applications ──────────────────────────────────────────────────────────────
export interface ApplicantDetail {
  id:         number;
  full_name:  string;
  email:      string;
  avatar?:    string | null;
  degree:     string;
  university: string;
}
export interface Application {
  id:                number;
  job:               number;
  job_detail?:       Job;
  candidate_detail?: ApplicantDetail;
  status:            "applied" | "reviewed" | "shortlisted" | "rejected";
  match_score:       number;
  cover_note:        string;
  applied_at:        string;
}

export const applications = {
  list: () =>
    request<Application[] | { results: Application[]; count: number }>("/api/applications/"),
  create: (jobId: number, coverNote = "") =>
    request<Application>("/api/applications/", "POST", { job: jobId, cover_note: coverNote }),
  updateStatus: (id: number, status: Application["status"]) =>
    request<Application>(`/api/applications/${id}/`, "PATCH", { status }),
  withdraw: (id: number) =>
    request<void>(`/api/applications/${id}/`, "DELETE"),
};

// ── Recommendation feedback (thumbs up/down) ────────────────────────────────
export const feedback = {
  send: (job: number, signal: "up" | "down", score = 0, comment = "") =>
    request<{ id: number; job: number; signal: string }>(
      "/api/feedback/", "POST", { job, signal, score, comment },
    ),
};

// ── Saved jobs (bookmarks) ──────────────────────────────────────────────────
export interface SavedJob {
  id:          number;
  job:         number;
  job_detail?: Job;
  created_at:  string;
}

export const savedJobs = {
  list: () =>
    request<SavedJob[] | { results: SavedJob[]; count: number }>("/api/saved-jobs/"),
  save: (jobId: number) =>
    request<SavedJob>("/api/saved-jobs/", "POST", { job: jobId }),
  unsave: (id: number) =>
    request<void>(`/api/saved-jobs/${id}/`, "DELETE"),
};

// ── Notifications ─────────────────────────────────────────────────────────────
export interface AppNotification {
  id:                number;
  job_id:            number;
  job_title:         string;
  job_company:       string;
  notification_type: "job_match" | "high_priority" | "recruiter_alert";
  match_score:       number;
  match_data: {
    matched_skills:      string[];
    missing_skills:      string[];
    reasons:             string[];
    explanation_summary: string;
  };
  sent_at:    string;
  is_read:    boolean;
  email_sent: boolean;
}

export const notifications = {
  list:        (unreadOnly = false) =>
    request<AppNotification[]>(`/api/notifications/${unreadOnly ? "?unread=1" : ""}`),
  unreadCount: () =>
    request<{ unread: number; high_priority: number }>("/api/notifications/unread-count/"),
  markRead:    (id: number) =>
    request<{ id: number; is_read: boolean }>(`/api/notifications/${id}/read/`, "PATCH"),
  markAllRead: () =>
    request<{ marked_read: number }>("/api/notifications/read-all/", "POST"),
  analytics:   () =>
    request<Record<string, number>>("/api/notifications/analytics/"),
};

// ── Admin panel ─────────────────────────────────────────────────────────────
export interface Paginated<T> {
  count:    number;
  next:     string | null;
  previous: string | null;
  results:  T[];
}
export interface AdminUser {
  id:           number;
  email:        string;
  full_name:    string;
  role:         UserRole;
  is_active:    boolean;
  is_staff:     boolean;
  date_joined:  string;
  skills_count: number;
}
export interface AdminApplication extends Application {
  candidate_email: string;
}
export interface AdminResume extends Resume {
  candidate_email: string;
}
export interface AdminStats {
  users:        { total: number; candidates: number; employers: number; admins: number; active: number };
  jobs:         { total: number; active: number };
  applications: number;
  skills:       number;
  resumes:      number;
}

function adminQuery(page = 1, search = "", pageSize?: number): string {
  const p = new URLSearchParams();
  p.set("page", String(page));
  if (search) p.set("search", search);
  if (pageSize) p.set("page_size", String(pageSize));
  return `?${p.toString()}`;
}

export interface ModelMetrics {
  version:             number | null;
  accuracy:            number;
  auc:                 number;
  n_samples:           number;
  n_candidates:        number;
  positives:           number;
  negatives:           number;
  feature_importances: Record<string, number>;
}
export interface ModelVersionRow extends Omit<ModelMetrics, "version"> {
  version:    number;
  is_active:  boolean;
  trained_at: string;
}

export const admin = {
  stats: () => request<AdminStats>("/api/admin/stats/"),
  retrain: (samples = 800) =>
    request<ModelMetrics>("/api/admin/retrain/", "POST", { samples }),
  modelVersions: () =>
    request<ModelVersionRow[]>("/api/admin/model-versions/"),
  rollback: (version: number) =>
    request<{ version: number; is_active: boolean }>("/api/admin/model-versions/rollback/", "POST", { version }),

  users: {
    list:   (page = 1, search = "", pageSize?: number) =>
      request<Paginated<AdminUser>>(`/api/admin/users/${adminQuery(page, search, pageSize)}`),
    create: (data: { email: string; full_name: string; role: UserRole; password?: string; is_active?: boolean }) =>
      request<AdminUser>("/api/admin/users/", "POST", data),
    update: (id: number, data: Partial<AdminUser> & { password?: string }) =>
      request<AdminUser>(`/api/admin/users/${id}/`, "PATCH", data),
    remove: (id: number) =>
      request<void>(`/api/admin/users/${id}/`, "DELETE"),
  },

  jobs: {
    list:   (page = 1, search = "", pageSize?: number) =>
      request<Paginated<Job>>(`/api/admin/jobs/${adminQuery(page, search, pageSize)}`),
    create: (data: JobCreatePayload) =>
      request<Job>("/api/admin/jobs/", "POST", data),
    update: (id: number, data: Partial<JobCreatePayload> & { is_active?: boolean }) =>
      request<Job>(`/api/admin/jobs/${id}/`, "PATCH", data),
    remove: (id: number) =>
      request<void>(`/api/admin/jobs/${id}/`, "DELETE"),
  },

  applications: {
    list:   (page = 1, search = "", pageSize?: number) =>
      request<Paginated<AdminApplication>>(`/api/admin/applications/${adminQuery(page, search, pageSize)}`),
    update: (id: number, status: Application["status"]) =>
      request<AdminApplication>(`/api/admin/applications/${id}/`, "PATCH", { status }),
    remove: (id: number) =>
      request<void>(`/api/admin/applications/${id}/`, "DELETE"),
  },

  skills: {
    list:   (page = 1, search = "", pageSize?: number) =>
      request<Paginated<{ id: number; name: string; slug: string; category: string }>>(
        `/api/admin/skills/${adminQuery(page, search, pageSize)}`),
    create: (data: { name: string; category?: string }) =>
      request<{ id: number; name: string; slug: string; category: string }>("/api/admin/skills/", "POST", data),
    update: (id: number, data: { name?: string; category?: string }) =>
      request<{ id: number; name: string; slug: string; category: string }>(`/api/admin/skills/${id}/`, "PATCH", data),
    remove: (id: number) =>
      request<void>(`/api/admin/skills/${id}/`, "DELETE"),
  },

  resumes: {
    list:   (page = 1, search = "", pageSize?: number) =>
      request<Paginated<AdminResume>>(`/api/admin/resumes/${adminQuery(page, search, pageSize)}`),
    remove: (id: number) =>
      request<void>(`/api/admin/resumes/${id}/`, "DELETE"),
  },
};
