# SkillMatch Nepal — API Documentation & Final Verification

> Step 5 deliverable · Backend: Django 5 + DRF + SimpleJWT · Frontend: Next.js 14 · DB: PostgreSQL (SQLite for dev) · Generated 2026-06-10

---

## 1. Final Connection Matrix

Every frontend call now has a working, shape-verified backend endpoint.

| Frontend (lib/api.ts) | Backend endpoint | Status |
|---|---|---|
| `auth.login` | `POST /api/auth/login/` | ✅ |
| `auth.register` | `POST /api/auth/register/` | ✅ |
| `auth.me` | `GET /api/auth/me/` | ✅ |
| `tryRefresh` | `POST /api/auth/refresh/` (+ `/api/auth/token/refresh/` alias) | ✅ fixed |
| `auth.profile` / `auth.updateProfile` | `GET/PUT/PATCH /api/auth/profile/` | ✅ fixed (PUT added, education fields exposed) |
| `resumes.upload` | `POST /api/resumes/` (multipart) | ✅ |
| `resumes.ats` | `GET /api/resumes/{id}/ats/` | ✅ |
| `resumes.list` | `GET /api/resumes/` (paginated) | ✅ fixed (FE type) |
| `resumes.analyze` | `POST /api/resumes/analyze/` | ✅ |
| `jobs.list` | `GET /api/jobs/?search=&job_type=` | ✅ fixed (salary_min/max, requirements, created_at added) |
| `jobs.get` | `GET /api/jobs/{id}/` | ✅ |
| `jobs.create` | `POST /api/jobs/` | ✅ fixed (payload no longer dropped, salary validation) |
| `applications.list/create/withdraw` | `GET/POST/DELETE /api/applications/` | ✅ **newly wired** (Apply button) |
| `matching.recommendations` | `GET /api/matching/recommendations/` | ✅ |
| `matching.jobCandidates` | `GET /api/matching/jobs/{id}/candidates/` | ✅ fixed (nested candidate object) |
| `matching.skillGap` | `GET /api/matching/skill-gap/{id}/` | ✅ |
| `matching.dashboard` | `GET /api/matching/dashboard/` | ✅ |
| `matching.careerRecommendations` | `GET /api/matching/career-recommendations/` | ✅ (client ready, no page consumes yet) |
| `matching.explain` | `GET /api/matching/explain/{id}/` | ✅ (client ready) |
| `notifications.*` (list, unread-count, mark read, mark all) | `/api/notifications/...` | ✅ fixed (missing migrations created) |
| `notifications.analytics` | `GET /api/notifications/analytics/` | ✅ fixed (`posted_jobs` → `jobs` bug) |
| — | `GET /api/health/`, `/api/docs/`, `/api/schema/`, `/api/skills/` CRUD | 🔸 backend-only (ops/docs/admin) |

---

## 2. Mini API Reference

Auth: `Authorization: Bearer <access>` unless marked Public. Errors always return the envelope
`{"error": {"code", "message", "status", "details?", "request_id"}}`.

### Auth

**POST `/api/auth/register/`** — Public
Body: `{"email", "full_name", "password", "role": "candidate"|"employer"}`
→ `201 {"id": 7, "email": "...", "full_name": "...", "role": "candidate", ...}`

**POST `/api/auth/login/`** — Public
Body: `{"email", "password"}` → `200 {"access": "<jwt>", "refresh": "<jwt>"}` (access 60 min, refresh 7 days)

**POST `/api/auth/refresh/`** (alias: `/api/auth/token/refresh/`) — Public
Body: `{"refresh"}` → `200 {"access"}`

**GET `/api/auth/me/`** → `200 {"id", "email", "full_name", "role", "candidate_profile", "employer_profile"}`

**GET/PUT/PATCH `/api/auth/profile/`** — role-aware (candidate or employer profile)
Candidate body (all optional): `{"degree", "college", "university", "graduation_year", "cgpa", "district", "province", "preferred_role", "github_url", "linkedin_url", "expected_salary_min", "expected_salary_max", ...}`
Read-only: `ats_score`, `hiring_probability`, `resume_score`.

### Resumes (candidate only)

**POST `/api/resumes/`** — multipart `{file, is_primary}` (PDF/DOCX/DOC/TXT ≤10 MB)
→ `201 {"id", "original_filename", "raw_text", "extracted_skills": [...], "is_primary", "uploaded_at"}`

**GET `/api/resumes/{id}/ats/`**
→ `200 {"ats_score": 78, "completeness_score", "keyword_score", "formatting_score", "experience_score", "strengths": [], "weaknesses": [], "recommendations": [], "section_scores": {}, "missing_sections": []}`

**GET `/api/resumes/`** → paginated `{count, results: [...]}` · **POST `/api/resumes/analyze/`** `{"text"}` → ATS result

### Jobs

**GET `/api/jobs/`** — Public. Query: `?search=` `?job_type=full_time|part_time|internship|contract` `?location=` `?ordering=`
→ `200 {"count": 5002, "next", "previous", "results": [Job]}`
Job: `{"id", "title", "company", "description", "requirements", "location", "job_type", "job_type_display", "salary_text", "salary_min": 40000, "salary_max": 80000, "required_skills": [], "is_active", "posted_at", "created_at", "employer_email"}`

**POST `/api/jobs/`** — Employer
Body: `{"title"*, "description"*, "company", "location", "job_type", "requirements", "salary_min", "salary_max", "required_skill_ids": []}`
Validation: `salary_min ≤ salary_max` else `400`. → `201 Job`

**GET/PATCH/DELETE `/api/jobs/{id}/`** — owner-only for writes

### Applications

**POST `/api/applications/`** — Candidate
Body: `{"job": <id>, "cover_note"?}` → `201 {"id", "job", "status": "applied", "match_score", "applied_at"}`
`400` if already applied or job inactive. Match score auto-computed (0 fallback if scoring fails).

**GET `/api/applications/`** — candidate sees own; employer sees applications to their jobs (paginated)
**PATCH `/api/applications/{id}/`** `{"cover_note"}` · **DELETE** withdraws

### Matching / AI (candidate unless noted)

**GET `/api/matching/recommendations/?limit=20`** → `200 [{"job": Job, "score": 87, "similarity": 82, "matched_skills": []}]`
**GET `/api/matching/jobs/{job_id}/candidates/`** — Employer, own job only
→ `200 [{"candidate": {"id", "email", "full_name", "role", "degree", "university", "cgpa"}, "candidate_id", "candidate_name", "candidate_email", "score", "similarity", "matched_skills"}]`
**GET `/api/matching/skill-gap/{job_id}/`** → `{"job_id", "job_title", "company", "matched_skills", "missing_skills", "missing_technologies", "missing_certifications", "experience_gaps", "match_improvement_pct"}`
**GET `/api/matching/career-recommendations/`** → `{"recommended_roles": [{"role", "confidence", "confidence_pct", "reason", "missing_skills"}], "learning_paths": [{"skill", "priority", "resources", "reason"}], "top_role"}`
**GET `/api/matching/explain/{job_id}/`** → feature-level score breakdown
**GET `/api/matching/dashboard/`** → composite `{"profile", "ats_analysis", "career_recommendations", "top_job_matches"}` (powers Dashboard + AI Insights pages)

### Notifications

**GET `/api/notifications/?unread=1&type=`** → `[{"id", "job_id", "job_title", "job_company", "notification_type", "match_score", "match_data": {"reasons", "matched_skills", ...}, "sent_at", "is_read", "email_sent"}]` (≤50)
**GET `/api/notifications/unread-count/`** → `{"unread": 3, "high_priority": 1}`
**PATCH `/api/notifications/{id}/read/`** · **POST `/api/notifications/read-all/`** → `{"marked_read": n}`
**GET `/api/notifications/analytics/`** — role-aware stats

### Ops

**GET `/api/health/`** — Public → `{"status": "ok", "checks": {"database": "ok"}}`
**GET `/api/docs/`** — Swagger UI · **GET `/api/schema/`** — OpenAPI 3.0

---

## 3. Environment Variables

### Backend (`skillmatch-backend/.env` — see `.env.example`)

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | dev value | **Required in production** (boot fails on default with DEBUG=0) |
| `DEBUG` | `1` | Set `0` in production (enables HSTS, secure cookies, SSL redirect) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated |
| `USE_SQLITE` / `SQLITE_PATH` | `0` / `./db.sqlite3` | Quick dev runs |
| `DB_NAME/USER/PASSWORD/HOST/PORT` | `skillmatch`/…/`5432` | PostgreSQL (production default) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Frontend origin(s) |
| `USE_REDIS` | `0` (off everywhere) | Redis removed for now; opt back in with `USE_REDIS=1`. Off → LocMem cache, DB sessions, task queue skipped |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache + Celery broker |
| `MATCHER_BACKEND` | `tfidf` | Works out of the box · `semantic`/`hybrid` (SBERT) opt-in |
| `THROTTLE_ANON` / `THROTTLE_USER` | `120/min` / `600/min` | API rate limits |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | — | SMTP (prod); console backend in dev |
| `LOG_LEVEL` | `DEBUG`/`INFO` | |

### Frontend (`skillmatch-frontend/.env.local`)

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` (dev) / your API origin (prod) |

---

## 4. Running End-to-End

```bash
# Backend
cd backend/skillmatch-backend
pip install -r requirements.txt
USE_SQLITE=1 python manage.py migrate
USE_SQLITE=1 python manage.py seed_synthetic   # optional: ~43k rows
USE_SQLITE=1 MATCHER_BACKEND=tfidf python manage.py runserver

# Frontend
cd frontend/skillmatch-frontend
npm install && npm run dev                      # http://localhost:3000
```

**Test accounts:** `cand@test.com` / `emp@test.com` (password `testpass123`); all 12,800 synthetic accounts use `Password123!`.

---

## 5. Verification Results (live, seeded DB)

| Check | Result |
|---|---|
| Health → database | ✅ 200 |
| Register (was 20 s Redis hang) | ✅ 201 in 0.5 s |
| Refresh, both paths | ✅ 200 / 200 |
| Job create with full FE payload | ✅ 201, all fields persisted |
| `salary_min > salary_max` | ✅ 400 |
| Profile PUT → GET round-trip | ✅ education fields persist |
| Apply → duplicate apply | ✅ 201 → 400 |
| Jobs list over 5,002 jobs | ✅ 200 in 95 ms (indexed) |
| Filtered search (`ML`, full-time) | ✅ 122 results |
| ML recommendations over 5k jobs | ✅ 200 in ~6 s (first call fits TF-IDF) |
| AI dashboard composite | ✅ 200 |
| Skill gap, notifications, analytics | ✅ 200 |
| Synthetic account login (12.8k users) | ✅ 200 |
| `makemigrations --check` | ✅ clean |

**Dataset:** 12,803 users · 12,802 profiles · 5,002 jobs · 9,001 applications · 3,000 notifications · 300 skills (~42,900 primary rows + 118k skill links).

## 6. ML Matching Pipeline (v2 — accuracy pass)

Improvements over the baseline per-request TF-IDF:

1. **Prebuilt corpus indexes** (`matching/index.py`) — the vectorizer is fitted once over all jobs (and all candidates for the employer view), version-keyed by cheap DB aggregates and rebuilt automatically on data change. In-process memory, no Redis.
2. **Better vectorizer** — 1–2 grams, sublinear TF, code-aware token pattern (keeps `c++`, `c#`, `node.js`, `ci-cd`).
3. **Skill normalization** — synonym map (`reactjs→react`, `k8s→kubernetes`, `postgres→postgresql`, …) and variant-suffix stripping before overlap comparison.
4. **Score calibration** — square-root transform spreads the raw 0.05–0.35 cosine band into a meaningful 0–100 score; overlap gets a small absolute-match bonus.
5. **Richer candidate documents** — resume text + profile summary + career objective + preferred role + normalized skills, so profile-only users match well.

**Measured on the 30k synthetic dataset** (`python manage.py evaluate_matcher --sample 100`; ground truth = job title contains candidate's preferred role):

| Metric | Baseline | v2 | Change |
|---|---|---|---|
| P@5 | 0.100 | **0.518** | 5.2× |
| Hit@5 | 0.375 | **0.970** | 2.6× |
| MRR | 0.292 | **0.768** | 2.6× |
| Latency (warm) | 4,660 ms | **~75 ms** | 62× faster |

API latency: recommendations/dashboard ~40 ms warm; candidate ranking over 12k profiles ~60 ms warm. Cold index builds (first request after boot or data change): ~6 s jobs, ~12 s candidates.

### Known limitations (honest notes for the thesis)

- First ML request after boot/data-change builds the index (seconds, see above); subsequent requests are milliseconds.
- Resume parsing is synchronous in the upload request; Celery offload activates only with `USE_REDIS=1` + a worker.
- `match_score` on an application falls back to 0 when the candidate has no resume (by design, never blocks the apply).
- Evaluation ground truth is synthetic (title ↔ preferred-role containment); real-world labels would refine the weights.
