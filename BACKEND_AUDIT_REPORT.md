# SkillMatch Nepal — Backend & ML Technical Audit

**Project:** ML-based resume ↔ job matching system for IT graduates in Nepal
**Stack:** Django 5 + DRF (backend), Next.js 14 App Router + TypeScript (frontend), scikit-learn / spaCy / sentence-transformers (ML), SQLite (dev) / PostgreSQL (opt-in)
**Auditor scope:** Read-only exploration, evidence-based scoring, no code changes.
**Date:** 2026-07-05

---

## 1. Repo Map (per Django app)

| App | Purpose (from code) | Evidence |
|-----|---------------------|----------|
| **accounts** | Custom `User` (email login, roles candidate/employer/admin) + rich `CandidateProfile` (25+ fields) + `EmployerProfile` + ML artefact tables (`CandidateEmbedding`, `ATSAnalysis`, `SkillGapReport`, `CareerRecommendation`). JWT via `simplejwt`, avatar/logo upload, delete-account (GDPR). | `accounts/models.py:14–200`, `accounts/urls.py:1–20`, `accounts/views.py:34–113` |
| **applications** | `Application` (candidate→job, status pipeline, auto-scored on submit) + `RecommendationFeedback` (thumbs up/down for retraining loop). Employer can advance status. | `applications/models.py:5–61`, `applications/views.py:16–85` |
| **common** | Cross-cutting infra: `RequestIDMiddleware`, permissions (`IsCandidate/IsEmployer/IsAdmin/IsOwnerOrReadOnly`), pagination, custom exception envelope, admin panel API (`admin_api.py`) and its URLs, `run_parallel` thread-pool helper, domain error classes. | `common/permissions.py:5–48`, `common/exceptions.py:106+`, `common/admin_api.py:1–226` |
| **config** | Django settings (SQLite default, opt-in Postgres/Redis), Celery app, root URLconf mounting all apps + Swagger. | `config/settings.py:82–99, 121–157`, `config/urls.py:14–33`, `config/celery.py` |
| **jobs** | `Job` model (title, description, requirements, salary, M2M skills, indexes), viewset with public list/retrieve, employer-only write, `?mine=true` filter. | `jobs/models.py:5–46`, `jobs/views.py:8–41` |
| **matching** | The ML core: TF-IDF / SBERT / hybrid engines (`engine/*`), skill extraction, NLP extractor, ranking model (RF + heuristic fallback), skill gap, career recommender, prebuilt indexes, training and evaluation commands. | `matching/services.py:139–233`, `matching/ranking_model.py:95–225`, `matching/engine/{tfidf,semantic,hybrid,factory}.py` |
| **notifications** | `Notification` + `EmailLog` models, list/read/analytics REST endpoints, Celery tasks (`evaluate_candidate_matches`, `evaluate_job_matches`, `send_match_email`, `daily_match_digest`), signals wired to Resume/Profile/Job saves, anti-spam guard (7-day cooldown, 5/day). | `notifications/tasks.py:77–206`, `notifications/services.py:22–85`, `notifications/signals.py:1–65` |
| **resumes** | `Resume` model (upload + raw_text + M2M extracted skills), viewset (candidate-only, multipart), `analyze/` endpoint, ATS analysis on-demand and auto on upload. Pipeline in `services.process_resume`. | `resumes/models.py:5–22`, `resumes/views.py:17–105`, `resumes/services.py:9–147` |
| **skills** | Simple `Skill` vocabulary (`name`, `slug`, `category`) with public read + auth write viewset. | `skills/models.py:5–19`, `skills/views.py:7–13` |

---

## 2. Per-module Audit

### 2.1 Authentication (accounts) — **8.5/10**

| Feature | Status | Evidence |
|---------|--------|----------|
| Custom User with email login + 3 roles | Implemented | `accounts/models.py:14–34` (`Role.CANDIDATE/EMPLOYER/ADMIN`, `USERNAME_FIELD="email"`) |
| JWT auth (access/refresh, 60 min / 7 d) | Implemented | `config/settings.py:153–157`; `accounts/urls.py:11–14`; alias `/token/refresh/` added for FE |
| Registration + role guard (no self-register admin) | Implemented | `accounts/serializers.py:18–20` explicitly rejects `role=admin` |
| Auto-create profile on signup | Implemented | `accounts/signals.py:7–15` (post_save) |
| Password validation | Implemented | `AUTH_PASSWORD_VALIDATORS` (4 validators), `validate_password` in serializer |
| GDPR delete | Implemented | `DeleteAccountView` at `/api/auth/me/delete/` |
| Avatar/logo upload with size + type check (5 MB, image/*) | Implemented | `accounts/views.py:18–52` |
| Profile PATCH/PUT | Implemented | `MyProfileView` at `/api/auth/profile/` |
| Permissions | Implemented | `IsCandidate/IsEmployer/IsAdmin` in `common/permissions.py:5–34` |
| Weakness | Missing | No password reset flow; no email verification; JWT blacklist not enabled; default `SECRET_KEY` present in `.env` |

### 2.2 Database Models — **8/10**

| App | Models | Key relations / constraints / indexes |
|-----|--------|---------------------------------------|
| accounts | `User`, `CandidateProfile`, `EmployerProfile`, `CandidateEmbedding`, `ATSAnalysis`, `SkillGapReport`, `CareerRecommendation` | O2O user↔profile; M2M `CandidateProfile.skills`; `SkillGapReport` has `unique_together=(user, job)`; `CandidateEmbedding` and `CareerRecommendation` are O2O with user |
| jobs | `Job` | FK employer; M2M `required_skills`; 3 explicit indexes (`is_active + posted_at`, `job_type`, `location`) — `jobs/models.py:34–38` |
| applications | `Application`, `RecommendationFeedback` | Both `unique_together=(candidate/user, job)`; ordered by recency |
| resumes | `Resume` | FK candidate; M2M extracted_skills; `is_primary` flag; ordered by uploaded_at |
| skills | `Skill` | unique name + auto-slug |
| notifications | `Notification`, `EmailLog` | 2 indexes on Notification (`candidate,is_read`; `candidate,job`); EmailLog indexed on (recipient, status) |
| matching | `ModelVersion` | Tracks training runs (accuracy, AUC, feature importances, active flag) |

**Gaps:** No index on `Application.candidate` / `Application.job` beyond ordering, no `db_index=True` on `Resume.candidate`, no PII encryption at rest. `CandidateEmbedding.vector` stored as JSON text (fine for small scale, does not scale to pgvector).

### 2.3 Resume upload & storage (resumes) — **8/10**

- Accepts PDF/DOCX/DOC/TXT via multipart. `ResumeViewSet` gates on `IsCandidate` (`resumes/views.py:19`).
- Upload flow: file saved, then `process_resume` called; failure logged but does NOT block upload (`resumes/views.py:42–47`).
- **Frontend enforces** 10 MB and file extension check (`app/upload/page.tsx:16, 65–78`). Backend does **not** enforce a size limit for resumes (only images have `MAX_IMAGE_BYTES=5MB`).
- Files go to `MEDIA_ROOT/resumes/`; served via Django static-file mount in DEBUG.
- **Security concerns:** no MIME sniffing server-side, no virus scan, no filename sanitisation beyond `original_filename` capture, no signed URLs on media.

### 2.4 Resume parser (parsing.py, analyzer.py, nlp/extractor.py, skill_extraction.py) — **6.5/10**

| Component | Real NLP? | Evidence |
|-----------|-----------|----------|
| `resumes/parsing.py` `extract_text` | Deterministic PDF/DOCX/TXT extraction via `pdfminer.six` + `python-docx` | `parsing.py:5–29` |
| `matching/skill_extraction.py` `extract_skills` | Dictionary + regex with alias table; case-insensitive, word-boundary | `skill_extraction.py:11–55` |
| `matching/nlp/extractor.py` `extract_resume_info` | Rule-based + optional spaCy NER (`en_core_web_sm/md`) for ORG/PERSON/GPE. Regex for email/phone/GitHub/LinkedIn/CGPA/year. spaCy is **optional** — silently returns nothing if the model isn't installed | `extractor.py:73–199` |
| `resumes/analyzer.py` `ATSScorer` | 5 pillars (completeness, keywords, formatting, experience, social) — regex/heuristic. Composite via fixed weights | `analyzer.py:92–215` |
| Education/experience/projects extraction | Only presence detection (regex per section header). No block parsing of dates, roles, companies, or bullet-level responsibilities | `extractor.py:19–31`, `resumes/services.py:58–97` |

**Verdict:** Hybrid dictionary + spaCy NER, not a learned resume-NER model. Education/experience/projects are **detected but not structured**. spaCy is a soft dependency.

### 2.5 ML pipeline — **7.5/10**

- **Real training code exists.** `matching/training.py:33–142` loads real DB candidates (min 30), builds 10 features per `FEATURE_ORDER`, labels pairs by skill overlap (≥0.40 pos, ≤0.12 neg), trains `RandomForestClassifier(n_estimators=300, max_depth=12, class_weight="balanced")`. Reports accuracy + ROC-AUC. Persists `ranker.joblib` + versioned `ranker_v<N>.joblib`, upserts `ModelVersion` row, calls `reload_model()`.
- **Gradient Boosting?** The docstring in `ranking_model.py:2–6` promises LightGBM/XGBoost/GBM fallback but `train_ranking_model` in `matching/training.py:100–104` only trains a **Random Forest**. **GBT claim is aspirational.**
- **Inference** (`ranking_model.py:169–187`): if the joblib is present, uses `model.predict_proba([vec])[0][1] * 100`; otherwise falls back to hand-tuned weighted heuristic.
- **Saved artefacts** (`matching/artifacts/`): a single `ranker.joblib` (1,084,345 bytes, modified 2026-06-28). No per-version files → only one training run executed.
- **Ranking model + hybrid matcher are two different scoring systems.** `matching.services.score_candidate_for_job` uses TF-IDF/SBERT hybrid + skill overlap (not the trained RF). Only `RecommendedJobsView` currently exposes the RF via `CandidateJobRanker.explain` on `/matching/explain/`. Application-time scoring also uses hybrid (`applications/views.py:39`).

### 2.6 Recommendation engine — **7.5/10**

| Engine | Implementation | Evidence |
|--------|----------------|----------|
| TF-IDF | scikit-learn `TfidfVectorizer` (1–2 grams, sublinear_tf) | `engine/tfidf.py:14–24` |
| SBERT semantic | `sentence-transformers all-MiniLM-L6-v2` singleton, cosine over normalised embeddings; **graceful fallback to TF-IDF** | `engine/semantic.py:24–52` |
| Hybrid | Weighted sum: `MATCHER_HYBRID_WEIGHTS = {tfidf:0.30, semantic:0.70}` | `engine/hybrid.py:26–43`, `settings.py:193` |
| Factory | `MATCHER_BACKEND` env var (default "tfidf") | `engine/factory.py:15–22` |
| Prebuilt index | Process-local TF-IDF index over jobs+candidates, versioned, thread-safe | `matching/index.py:81–120` |
| Skill normalisation | Synonym map + suffix strip | `services.py:26–61` |
| Final score | `w_sim·sqrt(sim) + w_overlap·overlap` × 100 | `services.py:71–93` |
| Explainable | Feature contributions, matched/missing skills, human reasons | `ranking_model.py:189–225` |

**Collaborative filtering?** **Not implemented.** The thesis specifies "hybrid recommendation (content + collaborative)". The only collaborative signal is `RecommendationFeedback` (thumbs up/down) — but nothing consumes it. → **Missing collaborative half.**

### 2.7 Complete API endpoint inventory (~45 endpoints)

| Method | Path | View | Auth |
|--------|------|------|------|
| GET | `/api/health/` | `HealthView` | Public |
| POST | `/api/auth/register/` | `RegisterView` | Public |
| POST | `/api/auth/login/` | `TokenObtainPairView` | Public |
| POST | `/api/auth/refresh/` (+ `/token/refresh/`) | `TokenRefreshView` | Public |
| GET | `/api/auth/me/` | `MeView` | Auth |
| DELETE | `/api/auth/me/delete/` | `DeleteAccountView` | Auth |
| GET/PATCH/PUT | `/api/auth/profile/` | `MyProfileView` | Auth |
| POST | `/api/auth/avatar/` | `AvatarUploadView` | Candidate |
| POST | `/api/auth/logo/` | `LogoUploadView` | Employer |
| CRUD | `/api/skills/` | `SkillViewSet` | Read pub / Write auth |
| CRUD | `/api/resumes/` | `ResumeViewSet` | Candidate |
| GET | `/api/resumes/{id}/ats/` | ATS action | Candidate |
| POST | `/api/resumes/analyze/` | `ResumeAnalyzeView` | Auth |
| CRUD | `/api/jobs/` | `JobViewSet` | Read pub / Write employer |
| CRUD | `/api/applications/` | `ApplicationViewSet` | Auth (create=Candidate) |
| POST | `/api/feedback/` | `FeedbackView` | Auth |
| GET | `/api/matching/recommendations/` | `RecommendedJobsView` | Candidate |
| GET | `/api/matching/jobs/{id}/candidates/` | `JobCandidatesView` | Employer |
| GET | `/api/matching/candidates/{id}/resume/` | `CandidateResumeView` | Employer/Admin |
| GET | `/api/matching/skill-gap/{job_id}/` | `SkillGapView` | Candidate |
| GET | `/api/matching/career-recommendations/` | `CareerRecommendationsView` | Candidate |
| GET | `/api/matching/explain/{job_id}/` | `ExplainMatchView` | Candidate |
| GET | `/api/matching/dashboard/` | `AIDashboardView` | Candidate |
| GET | `/api/notifications/` (+ unread-count, read-all, {id}/read, analytics) | notification views | Auth |
| GET | `/api/admin/stats/` | `AdminStatsView` | Admin |
| POST | `/api/admin/retrain/` | `AdminRetrainView` | Admin |
| GET | `/api/admin/model-versions/` (+ rollback) | version views | Admin |
| CRUD | `/api/admin/{users,jobs,applications,skills,resumes}/` | admin viewsets | Admin |
| GET | `/api/schema/`, `/api/docs/` | drf-spectacular | Public |

### 2.8 Candidate / Employer / Admin modules — **8/10 avg**

- **Candidate:** register, login, upload resume, view ATS, view recommendations, apply, skill-gap, career recs, explain match, feedback, view applications, edit profile, upload avatar, delete account.
- **Employer:** register, edit profile, upload logo, post jobs, see applicants, rank candidates, view candidate resume, update application status.
- **Admin:** Full CRUD viewsets for users/jobs/applications/skills/resumes, stats dashboard with `run_parallel` concurrent counts, one-click model retrain, model version history, rollback.

### 2.9 Security — **6.5/10**

| Item | Status |
|------|--------|
| JWT (simplejwt), 60 min access / 7 d refresh | Good |
| Role-based permission classes | Good |
| DRF throttling (Anon 120/min, User 600/min) | Good |
| Production hardening (HSTS, secure cookies, X-Frame DENY) gated on `not DEBUG` | Good |
| Startup guard rejecting insecure default SECRET_KEY when DEBUG=0 | Good |
| Request-ID middleware + structured logging | Good |
| Global exception handler that scrubs tracebacks | Good |
| CORS restricted to `CORS_ALLOWED_ORIGINS` | Good |
| **`.env` ships `SECRET_KEY=change-me-in-production`** | **Red flag** |
| **DEBUG=1 in shipped .env** | Red flag for prod |
| **No PII-at-rest encryption**; CVs stored plain | Gap vs thesis "data privacy" |
| **No signed media URLs** | Gap |
| Duplicate `CORS_ALLOWED_ORIGINS` line in settings | Minor |
| **No password reset / email verification** | Missing |
| **No JWT blacklist / rotation** | Missing |
| **File upload safety** — no MIME sniff / virus scan | Gap |

### 2.10 Performance — **7/10**

- `JobViewSet.queryset` uses `select_related("employer").prefetch_related("required_skills")`.
- Recommendation/rank views use `select_related`/`prefetch_related` and the process-local TF-IDF `index.py`.
- `run_parallel` used in admin stats (10 concurrent count queries).
- Pagination enforced globally (`PAGE_SIZE=20`).
- Indexes present on `Job`, `Notification`, `EmailLog`.
- **N+1 risks:** `AIDashboardView.get` computes 4 heavy panels sequentially (not `run_parallel`).
- Caching: LocMem in dev, Redis opt-in. No decorators on hot recommendation endpoint.
- SBERT model is a singleton; first call slow but cached.

### 2.11 Notifications + Celery — **8/10**

- Full pipeline is real (`notifications/tasks.py:77–206`): eval matches → create notification → gated email + optional recruiter alert. Thresholds 60/80/90.
- Anti-spam: 7-day cooldown per user-job, 5 emails/day cap.
- Celery **optional** at import time via no-op `shared_task` shim (`tasks.py:19–29`).
- Beat schedule: daily digest at 08:00 Asia/Kathmandu.
- Signals fire on Resume/Profile/Job save. **Dispatch skipped when `USE_REDIS=0`** — notifications silently no-op in dev.

### 2.12 Management commands — **8/10**

| Command | Purpose | State |
|---------|---------|-------|
| `seed_admin` | Idempotent admin (`admin@skillmatch.com / Admin@12345`) | Works |
| `seed_demo` | Small demo dataset | Present |
| `seed_realistic` | 38 KTM skills + 10 candidates + 10 KTM jobs | Full impl |
| `seed_from_excel` | Import KTM IT-Graduate CVs.xlsx | Full impl |
| `seed_dataset_v3` | Bulk import 105k-row synthetic Excel (batched) | Full impl |
| `seed_synthetic` | 12k candidates + 5k jobs + 9k applications | Full impl |
| `train_ranker` | CLI wrapper on `train_ranking_model` | Works |
| `evaluate_matcher` | P@k, Hit@k, MRR on preferred_role labels | Works |
| `bias_audit` | 80% rule parity by college/province | Works |

---

## 3. ML Evaluation — Reality Check

- **Training runs.** RF trained on real DB candidates, accuracy + ROC-AUC computed and saved. Feature importances persisted.
- **Algorithms:** RandomForestClassifier only. GBT promised in docstrings but not present.
- **Metrics measured:** `train_ranking_model` → accuracy + ROC-AUC. `evaluate_matcher` → P@k, Hit@k, MRR on a heuristic ground truth ("candidate's `preferred_role` appears in job title" — thin proxy). No P/R/F1 in training.
- **Ground-truth labels are circular.** `training.py:79–84` labels a (candidate, job) pair positive when skill overlap ≥ 0.40 — but `skill_overlap` is also feature index 0 (`FEATURE_ORDER[0]`). The RF is essentially memorising a threshold on its own input, **inflating accuracy/AUC.** No labels from `RecommendationFeedback` or applications.
- **Artifacts on disk:** only `ranker.joblib` (1 MB, 2026-06-28). No versioned files, no embedding index.
- **Bias audit is real** (not stubbed): `bias_audit.py:39–104` samples candidates, groups by college & province, applies four-fifths rule, prints flagged groups. **Stdout only — no persistence.**
- **Explainability implemented:** per-feature contribution + matched/missing skills + human reasons, exposed at `/api/matching/explain/{job_id}/`.

---

## 4. Frontend Integration

### Pages under `app/`

| Route | File | Auth guard |
|-------|------|-----------|
| `/` | `app/page.tsx` | Public (`PublicHomeGate`) |
| `/login`, `/register` | | Public |
| `/dashboard` (+ `/ai-insights`) | | Candidate |
| `/jobs`, `/jobs/[id]` | | Auth |
| `/upload` | | Candidate |
| `/profile` | | Auth |
| `/recommended` | | Candidate |
| `/applications` | | Auth |
| `/employer` | | Employer |
| `/admin` + `/admin/{users,jobs,applications,resumes,skills}/` | | Admin |
| `/privacy` | | Public |

Global error boundaries present: `error.tsx`, `global-error.tsx`, `dashboard/error.tsx`, `admin/error.tsx`, `not-found.tsx`, `loading.tsx`.

### API client (`lib/api.ts`, 671 lines)

- Bearer token + auto-refresh on 401.
- `AbortController` timeout (30 s).
- `humanizeError` maps backend envelope → user string.
- Endpoints grouped: `auth`, `resumes`, `jobs`, `employerProfile`, `candidateProfile`, `matching`, `applications`, `feedback`, `notifications`, `admin`.

Spot-audited URLs: all match backend routes. Only drift: `ProfileResponse.technical_skills` (TS type) vs backend nested `skills` — unused elsewhere.

---

## 5. End-to-end flow — register → upload → parse → recommend

1. **Register.** POST `/api/auth/register/` → `RegisterSerializer.create`. `post_save` signal auto-creates `CandidateProfile`.
2. **Login.** `TokenObtainPairView` returns access+refresh. FE stores in `localStorage`.
3. **Upload resume.** POST `/api/resumes/` multipart. `perform_create` saves file, sets `is_primary`, calls `process_resume`.
4. **process_resume** (`resumes/services.py:9–56`): pdfminer text → dictionary skill match → profile fields via spaCy+regex → ATS score → SBERT embedding.
5. **Signal fires:** `on_resume_saved` → `_queue(evaluate_candidate_matches)`. Skipped if `USE_REDIS=0` (default) → **notifications silently no-op in dev.**
6. **Recommendations.** GET `/api/matching/recommendations/` → hybrid TF-IDF+overlap score, top-N returned. Rendered in `/recommended` and `/dashboard`.

**Flow works end to end.** But: trained RF ranker is NOT on this path — only `ExplainMatchView` uses it. **Two different score sources = inconsistency** between recommendations page and explain page.

---

## 6. Config check (settings.py)

| Item | Value | Note |
|------|-------|------|
| DB backend | SQLite by default (`.env` sets `USE_SQLITE=1`) | Thesis promises PostgreSQL |
| INSTALLED_APPS | admin, DRF, cors, filters, spectacular + 7 local | Complete |
| Auth model | `accounts.User` | OK |
| DRF auth | JWT + Session | OK |
| Pagination | `StandardPagination`, PAGE_SIZE=20 (double-assigned at 136 and 238) | Sloppy |
| Throttle | anon 120/min, user 600/min | Good |
| JWT lifetimes | Access 60m / Refresh 7d | Good |
| Matcher backend | Env `MATCHER_BACKEND=tfidf` (default) | Hybrid available but off |
| CORS | `http://localhost:3000` (double-set at 182 and 184) | Harmless dup |
| Cache | LocMem dev / Redis opt-in | OK |
| Celery broker | Redis | OK |
| Email | Console (dev), SMTP env-driven | OK |
| Beat | Daily digest 08:00 Nepal | OK |
| Logging | Rotating `logs/errors.log`, request_id filter | Good |
| Production hardening | HSTS, secure cookies gated on `not DEBUG` | Good |
| SECRET_KEY guard | Refuses `dev-insecure...` when DEBUG=0 | Good |
| Shipped `.env` SECRET_KEY | `change-me-in-production` | Weak |

---

## 7. Tests

- **accounts/tests.py:** 3 tests (register→profile, admin-blocked, login+me).
- **matching/tests.py:** 2 tests (skill-extraction variants, ML candidate ranks ML job first).
- **Zero tests** in: applications, resumes, jobs, common, notifications, skills. Ranking model, ATS scorer, skill-gap, career recommender, Celery tasks untested.
- **Total: ~5 tests.**

---

## 8. Existing docs summary

- **SkillMatch_Technical_Documentation.docx:** production-hardening changelog (exception handler, request-id middleware, ML endpoint guards, JSON 404/500, FE timeout + `humanizeError`, error boundaries; two "production bugs fixed": missing `recharts` dep, wrong `access_token` key on ai-insights).
- **Technical_Decision_Breakdown.docx:** thesis-defense guidance. Argues Python + Django + React + Postgres + scikit-learn/spaCy/SBERT + RF/GBT ranker. Describes 6-stage pipeline (ingest → clean → NER → vectorise → cosine + tree ensemble → evaluate with P/R/F1/MAP/NDCG). Codebase **partially** implements: parsing, hybrid vectorisation, cosine + RF present; NER is dictionary+spaCy (not custom NER); evaluation reports only P@k/Hit@k/MRR — **no MAP/NDCG/F1.**

---

## 9. Bugs / Red Flags Spotted

1. **Training labels are circular.** `training.py:79–84` labels pairs positive when skill_overlap ≥ 0.40 — but `skill_overlap` is also feature 0. The RF memorises a threshold on its own input; AUC is inflated.
2. **Train/serve skew.** `training.py:87` sets `semantic_sim=0.0` during training, but inference (`ranking_model._build_features`) computes real SBERT sim. Feature distribution differs at test time.
3. **Ranker not used on recommendation path.** `/recommendations/` uses hybrid + overlap; only `/explain/` uses the RF. Users see one score, employers see another.
4. **GBT promised but absent.**
5. **No collaborative filtering.** `RecommendationFeedback` model exists but no code consumes it.
6. **`Application.match_score` uses hybrid**, not RF — inconsistent numbers across surfaces.
7. **spaCy silent dependency.** Missing model → empty ORG/PERSON/GPE, no admin warning.
8. **Backend accepts unlimited resume file size.** FE caps at 10 MB but raw curl bypasses.
9. **`SECRET_KEY=change-me-in-production` committed in `.env`.**
10. **Duplicate `CORS_ALLOWED_ORIGINS` and `PAGE_SIZE` assignments** in settings.py.
11. **`AIDashboardView` recomputes career recs synchronously** on first hit — heavy call, no cache.
12. **Notification signals no-op in dev** because `NOTIFY_ASYNC = USE_REDIS = 0`.
13. **`ProfileResponse.technical_skills`** (TS type) doesn't match backend serializer field.
14. **`CandidateEmbedding.vector` stored as JSON text** — no vector DB.
15. **Media served in DEBUG only** — production media serving unconfigured.

---

## 10. Security findings (summary)

- Weak default SECRET_KEY in shipped `.env` (mitigated by startup guard when DEBUG=0, but plaintext in repo).
- Default admin credentials `admin@skillmatch.com / Admin@12345` in `seed_admin` — must rotate before deploy.
- No PII encryption; CV files plain on disk.
- No JWT blacklist; refresh tokens valid 7 days after logout.
- No email verification; no password-reset flow.
- No signed media URLs.
- Login rate limit generous (120/min anon) — weak brute-force protection.
- **Positive:** request-ID log correlation, no traceback leak, HSTS in prod, throttling, role-based permissions, cascading FKs on user delete for GDPR.

---

## 11. Thesis-requirement mapping

| Thesis requirement | Status | Evidence |
|---------------------|--------|----------|
| Candidate / Employer / Admin roles | Implemented | `accounts/models.py:14–22`, `common/permissions.py`, `common/admin_api.py` |
| Resume upload + NLP parsing (skills/education/projects/experience) | Partial — skills yes; education partly; projects/experience only presence-detected | `resumes/services.py`, `matching/nlp/extractor.py` |
| ML matching (Random Forest / Gradient Boosting) | RF only; GBT missing | `matching/training.py:100`, `ranking_model.py:2` |
| Hybrid recommendation (content + collaborative) | Content-only (TF-IDF + SBERT); no collaborative | `matching/services.py`; `RecommendationFeedback` unused |
| Explainable scores | Implemented | `matching/ranking_model.py:189–225`, `/api/matching/explain/` |
| Bias mitigation | Audit tool present, no in-model mitigation | `matching/management/commands/bias_audit.py` |
| Data privacy | GDPR delete + role gating done; no PII encryption, plain CVs | `DeleteAccountView` |
| JWT auth | Implemented | simplejwt configured |
| DRF APIs | ~45 endpoints | See §2.7 |
| PostgreSQL | Supported but SQLite is default | `settings.py:82–99` |
| React frontend | Next.js 14, 15+ pages | `frontend/skillmatch-frontend/app/` |
| Precision/Recall/F1 evaluation | Only P@k/Hit@k/MRR + accuracy/AUC | `evaluate_matcher.py` |
| MAP / NDCG | Missing | — |
| Sentence-BERT semantic matching | Implemented | `matching/engine/semantic.py` |
| Nepal-context skill dictionary | Implemented | `seed_realistic.py`, `career_recommender.ROLE_SKILL_MAP` |
| Notifications & email pipeline | Implemented | notifications app + Celery |
| Admin panel & model retrain UI | Implemented | `common/admin_api.py`, `/api/admin/retrain/` |

---

## 12. Module scoreboard

| Module | Score | Note |
|--------|-------|------|
| Authentication | 8.5/10 | Solid; missing reset/verify/blacklist |
| Database models | 8/10 | Rich; needs a few more indexes, no PII crypto |
| Resume upload & storage | 8/10 | Works; no size limit / MIME sniff |
| Resume parser (NLP) | 6.5/10 | Dictionary + spaCy; no structured experience |
| ML pipeline | 7.5/10 | RF trains, but circular labels + no GBT |
| Recommendation engine | 7.5/10 | Content only, no collab |
| APIs | 9/10 | Comprehensive, well-organised |
| Candidate/Employer/Admin | 8/10 | All flows work |
| Security | 6.5/10 | Good primitives, weak defaults + no crypto |
| Performance | 7/10 | Prefetches good, some heavy handlers |
| Notifications/Celery | 8/10 | Real pipeline, silent in dev |
| Management commands | 8/10 | Rich seeding + train/eval/audit |
| Tests | 3/10 | 5 tests total |
| Explainability | 8/10 | Feature contributions + reasons |
| Bias audit | 7/10 | Real 80% rule, stdout only |
| Frontend integration | 8.5/10 | Typed client, refresh handling, error boundaries |

**Overall completion vs thesis scope: ~75%.**

---

## 13. Working features

- Full candidate journey: register → JWT → PDF upload → parse → skill extraction → ATS score → recs → apply → feedback.
- Full employer journey: register → post job → applicants → rank candidates → view resume.
- Admin CRUD + retrain + version rollback.
- Global exception envelope + request-ID tracing.
- Hybrid matcher (TF-IDF + SBERT + weighted blend).
- Trained RF ranker on disk, lazy-loaded.
- Explainable AI: per-feature contribution + reasons.
- Skill gap + career recs + AI dashboard.
- Bias audit CLI (80% rule).
- 8 seed commands (demo → real → synthetic 105k).
- Frontend: global error boundaries, toasts, auth context, typed API client with token refresh.
- Notifications pipeline with anti-spam guards.

## 14. Partial features

- Resume parsing: contact/degree/CGPA/links yes; dated experience blocks no.
- ML ranker: RF trained but with weak labels; GBT unimplemented.
- Evaluation: ranking metrics only; no F1/MAP/NDCG for skill extraction.
- Bias mitigation: audit only, no in-training mitigation.
- Postgres: supported by config, but dev+shipped `.env` uses SQLite.
- Notifications: wired but silent unless `USE_REDIS=1`.

## 15. Missing features

- Collaborative filtering consuming `RecommendationFeedback` or `Application` rows.
- Precision/recall/F1 for skill extraction; MAP; NDCG.
- LightGBM/XGBoost/GBM ranker.
- Password reset, email verification, JWT blacklist.
- PII-at-rest encryption, signed media URLs, virus scan.
- Backend-side resume size limit.
- Persisted evaluation reports (currently stdout only).

---

## 16. Prioritized Roadmap

### Critical (thesis-defense blockers)
1. **Fix training labels.** Replace overlap-threshold pseudo-labels with real signals from `Application.status` (applied/shortlisted = positive; rejected = negative) or `RecommendationFeedback.signal`. Currently RF learns a tautology. — `matching/training.py:79–84`.
2. **Report Precision/Recall/F1 + MAP + NDCG** (thesis explicitly names them). Extend `evaluate_matcher.py`, persist to `ModelVersion.evaluation` JSON.
3. **Wire the trained ranker into recommendations.** Either re-rank top-N with the RF, or use hybrid everywhere and drop the RF — the current split is inconsistent and confusing to a defender.
4. **Implement a collaborative signal.** Even simple "users who applied to X also applied to Y" from `Application` rows fulfils the hybrid thesis requirement.
5. **Rotate SECRET_KEY** and remove the plaintext default from `.env`; document strong-key generation in README.

### High
6. Switch default to PostgreSQL (`USE_SQLITE=0`) and prove it runs — the thesis says Postgres.
7. Add tests for `applications`, `resumes`, `notifications`, `ranking_model`, `skill_gap`, `career_recommender` (5 tests total right now).
8. Add server-side resume file-size (10 MB), MIME sniffing, filename sanitisation.
9. Replace `semantic_sim=0.0` at train time with real SBERT sim — remove train/serve skew (`training.py:87`).
10. Extract dated education + experience blocks (per-role date + duties) — closes the biggest parser gap.
11. Persist evaluation and bias-audit runs to `ModelVersion` or a new `EvaluationReport` model; expose in admin UI.

### Medium
12. Add JWT blacklist + logout that revokes refresh.
13. Password reset + email verification.
14. Turn on Redis for prod; enable `NOTIFY_ASYNC`.
15. Signed media URLs or S3/GCS pre-signed downloads.
16. Add MAP@k and NDCG@k to `evaluate_matcher`.
17. Add LightGBM as second trained model; compare RF vs LGBM in the thesis chapter.
18. Fix `ProfileResponse.technical_skills` type mismatch in FE.
19. Deduplicate `CORS_ALLOWED_ORIGINS` and `PAGE_SIZE` assignments in `settings.py`.
20. Move dashboard panels into `run_parallel` in `AIDashboardView.get`.

### Low
21. Tighter rate-limit on `/api/auth/login/`.
22. Cache SBERT + TF-IDF vectorizer to disk (`joblib`) between process restarts.
23. spaCy install probe + admin banner when NER unavailable.
24. `db_index=True` on `Application.candidate` and `Application.job`.
25. Add MyPy/ruff to CI.
26. Add `db.sqlite3` to `.gitignore`.

---

## Bottom line

The codebase is real, non-trivial, and ships **almost every feature the thesis describes** at least in skeleton form — RF ranker artefact on disk, SBERT semantic matcher, admin retrain UI, bias-audit CLI, polished Next.js frontend, ~45 endpoints, all three roles fully wired.

Two headline weaknesses versus the thesis:

- **ML rigor:** circular training labels, missing GBT, no collaborative half of the "hybrid" recommender.
- **Evaluation depth:** thinner than promised — no F1 / MAP / NDCG.

Fixing the training-label loop, wiring the RF into the actual recommendation path, and adding the missing metrics moves this from "good FYP" to "defensible thesis." That is the priority order.
