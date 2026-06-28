# SkillMatch Nepal — API Reference (by Category)

Base URL (local dev): `http://127.0.0.1:8000`
Interactive docs: `http://127.0.0.1:8000/api/docs/` (Swagger) · Schema: `/api/schema/`

**Auth model:** JWT (Bearer). Obtain a token from `POST /api/auth/login/`, then send
`Authorization: Bearer <access_token>` on protected requests.

**Roles:** `Candidate` (job seeker) and `Employer`. Some endpoints are role-restricted —
shown in the *Access* column.

---

## 1. System & Operational

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/health/` | Public | Liveness/health check. |
| GET | `/api/schema/` | Public | OpenAPI 3 schema (machine-readable). |
| GET | `/api/docs/` | Public | Swagger UI for exploring & testing the API. |
| —   | `/admin/` | Staff | Django admin site. |

---

## 2. Authentication & Account  ·  `/api/auth/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/auth/register/` | Public | Create an account (candidate or employer). |
| POST | `/api/auth/login/` | Public | Obtain JWT `access` + `refresh` tokens. |
| POST | `/api/auth/refresh/` | Public | Exchange a `refresh` token for a new `access` token. |
| POST | `/api/auth/token/refresh/` | Public | Alias of `/refresh/` (kept in sync with the frontend). |
| GET | `/api/auth/me/` | Authenticated | Current user (id, email, role). |
| GET | `/api/auth/profile/` | Authenticated | Retrieve the signed-in user's profile. |
| PATCH | `/api/auth/profile/` | Authenticated | Partial update of the profile. |
| PUT | `/api/auth/profile/` | Authenticated | Full update of the profile. |

---

## 3. Skills  ·  `/api/skills/`

Shared skill vocabulary used by both resumes and jobs. Reads are public; writes require login.

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/skills/` | Public | List all skills. |
| POST | `/api/skills/` | Authenticated | Create a skill. |
| GET | `/api/skills/{id}/` | Public | Retrieve one skill. |
| PUT / PATCH | `/api/skills/{id}/` | Authenticated | Update a skill. |
| DELETE | `/api/skills/{id}/` | Authenticated | Delete a skill. |

---

## 4. Resumes  ·  `/api/resumes/`  *(Candidate only)*

Upload a PDF/DOCX resume; the server parses text and extracts skills.

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/resumes/` | Candidate | List the candidate's own resumes. |
| POST | `/api/resumes/` | Candidate | Upload a resume (multipart file). Auto-parses + extracts skills. |
| GET | `/api/resumes/{id}/` | Candidate | Retrieve one resume (parsed text, skills). |
| PUT / PATCH | `/api/resumes/{id}/` | Candidate | Update a resume. |
| DELETE | `/api/resumes/{id}/` | Candidate | Delete a resume. |
| GET | `/api/resumes/{id}/ats/` | Candidate | ATS-style analysis for the resume. |
| POST | `/api/resumes/analyze/` | Authenticated | Analyze raw resume text/file without saving it. |

---

## 5. Jobs  ·  `/api/jobs/`

Public can browse active jobs; employers manage their own postings.

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/jobs/` | Public | List jobs (public sees active only; employers see all of their own). |
| POST | `/api/jobs/` | Employer | Create a job posting. |
| GET | `/api/jobs/{id}/` | Public | Retrieve one job. |
| PUT / PATCH | `/api/jobs/{id}/` | Employer (owner) | Update own job. |
| DELETE | `/api/jobs/{id}/` | Employer (owner) | Delete own job. |

**Query params:** `search=` (title, company, description, location) ·
`job_type=`, `is_active=`, `location=` (filters) · `ordering=posted_at|title`.

---

## 6. Applications  ·  `/api/applications/`

Candidates apply to jobs; each application is auto-scored against the job at submit time.

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/applications/` | Authenticated | Candidates see their own; employers see applications to their jobs. |
| POST | `/api/applications/` | Candidate | Apply to a job (rejects duplicates; sets `match_score`). |
| GET | `/api/applications/{id}/` | Authenticated | Retrieve one application. |
| PATCH | `/api/applications/{id}/` | Authenticated | Update (e.g., employer changes status). |
| DELETE | `/api/applications/{id}/` | Authenticated | Withdraw/remove an application. |

*(No `PUT` — this resource only allows `GET`, `POST`, `PATCH`, `DELETE`.)*
`status`, `match_score`, `applied_at` are read-only (server-set).

---

## 7. Matching & AI  ·  `/api/matching/`

The recommendation engine (TF-IDF + cosine by default; SBERT optional).

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/matching/recommendations/` | Candidate | Jobs recommended for the candidate, ranked. |
| GET | `/api/matching/jobs/{job_id}/candidates/` | Employer | Candidates ranked for a given job. |
| GET | `/api/matching/skill-gap/{job_id}/` | Candidate | Skills the candidate is missing for a job. |
| GET | `/api/matching/career-recommendations/` | Candidate | Suggested career paths / target roles. |
| GET | `/api/matching/explain/{job_id}/` | Candidate | Why this job matched (score breakdown). |
| GET | `/api/matching/dashboard/` | Candidate | Aggregated AI insights for the candidate. |

---

## 8. Notifications  ·  `/api/notifications/`

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/notifications/` | Authenticated | List the user's notifications. |
| GET | `/api/notifications/unread-count/` | Authenticated | Count of unread notifications. |
| GET | `/api/notifications/analytics/` | Authenticated | Notification analytics summary. |
| POST | `/api/notifications/read-all/` | Authenticated | Mark all notifications read. |
| PATCH | `/api/notifications/{id}/read/` | Authenticated | Mark a single notification read. |

---

### Quick reference — endpoint count by category

| Category | Endpoints |
|----------|-----------|
| System & Operational | 4 |
| Authentication & Account | 8 |
| Skills | 5 |
| Resumes | 7 |
| Jobs | 5 |
| Applications | 5 |
| Matching & AI | 6 |
| Notifications | 5 |

> Generated from the project's `urls.py` and `views.py`. For live, always-current
> details (request/response bodies, status codes), use the Swagger UI at `/api/docs/`.
