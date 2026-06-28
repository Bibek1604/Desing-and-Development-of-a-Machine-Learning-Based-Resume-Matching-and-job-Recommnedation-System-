# SkillMatch — Blueprint vs. Implementation Gap Analysis

**Project:** ML-Based Resume Matching & Job Recommendation System
**Author:** Bibek Pandey · Coventry ID 14809712 · Module ST6000CEM
**Generated:** automated audit of `backend/skillmatch-backend` and `frontend/skillmatch-frontend`

This document maps the production blueprint to the current codebase: what is **matched** (the design is implemented as specified), what is **partial**, and what is **missing** — followed by what was closed in this pass and the remaining roadmap.

---

## 1. Executive coverage summary

The **core product and the ML/NLP engine** (Phases 1–4 of the blueprint) are largely built. The gaps are concentrated in **governance, the feedback loop, and production operations** (Phases 5–7) — much of which is external infrastructure rather than application code.

| Blueprint area | Coverage | Notes |
|---|---|---|
| Phase 1 — Data & NLP pipeline | ~85% | Parsing, skill extraction, taxonomy, structured profile all working. Dataset now 105k rows. |
| Phase 2 — ML models | ~85% | TF-IDF + BERT semantic + hybrid + trained RandomForest ranker + skill-gap + career engine. Bias testing was missing (now added). |
| Phase 3 — Backend API | ~90% | Auth, RBAC, jobs, applications, recommendations, admin, throttling, Celery, Redis all present. |
| Phase 4 — Frontend | ~85% | All candidate/employer/admin pages exist. Feedback UI was missing (now added). Kanban + dedicated tracker still partial. |
| Phase 5 — Testing | ~30% | Basic unit tests only; no integration/UAT/load-test suite. |
| Phase 6 — Deployment / Ops | out of scope | **This project runs locally only** (SQLite, `runserver`/`next dev`). Production hosting, Docker, CI, monitoring, and S3 are intentionally excluded. |
| Phase 7 — Feedback loop & governance | ~30% → improved | Feedback loop + bias audit added this pass. Model-versioning, audit logs remain (optional for local). |
| **Overall feature coverage (local scope)** | **~80%** | Strong application + ML core. Remaining items are governance niceties, not infrastructure. |

> **Scope note:** SkillMatch is run **on localhost** for this thesis. Production infrastructure from the blueprint (Docker, CI/CD, Prometheus/Grafana/Sentry, AWS S3, managed Postgres, load testing) is deliberately out of scope and has been removed from the plan below.

---

## 2. Detailed status by blueprint item

Legend: ✅ Implemented (matches blueprint) · 🟡 Partial · ❌ Missing · 🆕 Added in this pass

### Users, auth & security (Phase 3.3)
- ✅ Register / login with role selection (candidate / employer / admin) — `accounts/`
- ✅ JWT access (60 min) + refresh (7 days) — SimpleJWT
- ✅ Role-based access control on endpoints — `common/permissions.py`
- ✅ Password hashing (Django PBKDF2/bcrypt) — never plaintext
- ✅ Rate limiting (DRF throttling: 120/min anon, 600/min user)
- ✅ Input validation via DRF serializers; ORM prevents SQL injection
- 🟡 JWT in **localStorage**, blueprint specifies **httpOnly cookies** — security hardening item
- ❌ Email verification before first login
- ❌ Resume files on private **S3** with pre-signed URLs (currently local `MEDIA`)

### Data & NLP pipeline (Phase 1)
- ✅ PDF/DOCX/TXT text extraction — `resumes/parsing.py`
- ✅ Skill extraction + normalization / synonym taxonomy — `matching/skill_extraction.py`, `matching/services.py`
- ✅ Resume → structured profile (skills, education, links, bio) on upload — `resumes/services.py` + `matching/nlp/extractor.py`
- ✅ Section detection, NER (spaCy when available) — `matching/nlp/extractor.py`
- 🟡 Skill taxonomy is a hardcoded dict, not an editable table
- ✅ Dataset: **105,000 rows × 38 columns** synthetic + bulk seed command — `Synthetic_IT_CVs_105k_38col.xlsx`, `seed_dataset_v3`

### ML models & recommendation engine (Phase 2)
- ✅ TF-IDF matcher (1–2 gram, sublinear tf) — `matching/engine/tfidf.py`
- ✅ Semantic similarity (sentence-transformers MiniLM) — `matching/engine/semantic.py`
- ✅ Hybrid scoring (configurable weights) — `matching/engine/hybrid.py`, `matching/services.py`
- ✅ Content ranking model — RandomForest, trained via `train_ranker`, auto-loaded — `matching/ranking_model.py`
- ✅ Skill-gap analysis — `matching/skill_gap.py`
- ✅ Career recommendations (top-N roles) — `matching/career_recommender.py`
- ✅ ATS scoring — `resumes/analyzer.py`, `ATSAnalysis`
- ✅ Explainable match ("why this matches") — `matching/ranking_model.py explain()`
- 🆕 **Fairness / bias audit** (demographic parity by college/province) — `matching/management/commands/bias_audit.py`
- ❌ Collaborative-filtering term in the hybrid formula (uses content + semantic; CF needs interaction history)

### Backend API (Phase 3.2)
- ✅ `POST /api/auth/register`, `POST /api/auth/login`, refresh, `/me`, `/profile`
- ✅ `POST /api/resumes/` upload → triggers pipeline
- ✅ `GET /api/matching/recommendations/` ranked jobs
- ✅ `POST /api/jobs/`, `GET /api/jobs/`, `GET /api/matching/jobs/{id}/candidates/`
- ✅ Applications: apply / list / status / withdraw — `applications/`
- ✅ Admin: stats, users, jobs, applications, skills, resumes — `common/admin_*.py`
- ✅ Notifications + async matching (Celery) — `notifications/`
- 🆕 **`POST /api/feedback/`** thumbs up/down — `applications/` (RecommendationFeedback)
- ❌ `POST /api/admin/retrain/` one-click retrain endpoint (CLI command exists: `train_ranker`)

### Frontend (Phase 4)
- ✅ Register/login, profile setup + resume upload, recommendations, job detail + apply, dashboard, AI insights
- ✅ Employer: post job, my postings, company profile, ranked candidates
- ✅ Admin dashboard + CRUD pages
- 🆕 **Feedback thumbs** on recommendation cards
- 🟡 Application tracker is embedded in dashboard, not a dedicated page
- 🟡 Hiring pipeline shows ranked cards, not a drag-drop Kanban
- ❌ Consent form before upload, privacy-policy page, account self-deletion UI

### Governance, testing & ops (Phases 5–7)
- 🟡 Unit tests for auth + matching only — no integration/UAT/load suite
- 🆕 **Dockerfile + docker-compose (web/db/redis) + GitHub Actions CI**
- ❌ Prometheus + Grafana, Sentry, UptimeRobot — external monitoring infra
- ❌ Model-versioning table + drift monitor + blue-green promotion
- ❌ Audit-log table for all user actions
- ❌ Automated S3 backups, disaster-recovery runbook
- ❌ GDPR right-to-delete + data-retention purge jobs

---

## 3. Closed in this pass

1. **Feedback loop** — `RecommendationFeedback` model, `POST /api/feedback/`, and thumbs up/down on recommendation cards. This is the signal source the retraining loop (Phase 7) needs.
2. **Bias / fairness audit** — `python manage.py bias_audit` computes recommendation/representation parity by college and province and flags any group below the 80% threshold (blueprint Step 2.4).
3. **Local-only setup** — runs on SQLite with `runserver` + `next dev`. Infrastructure/Docker/CI removed.
4. **Optimised ranker** — RandomForest trained on the seeded dataset and shipped as `matching/artifacts/ranker.joblib`, auto-loaded by the app.

## 4. Remaining roadmap (local scope, priority order)

1. Admin **retrain** endpoint that runs `train_ranker` + a `ModelVersion` table recording metrics per run.
2. Dedicated **My Applications** tracker page + employer **Kanban** (statuses already exist in the model).
3. GDPR niceties: account-deletion button, consent checkbox before upload, privacy-policy page.
4. `AuditLog` model logging mutating requests.
5. Email verification (optional locally; needs an SMTP provider).

---

*The application and ML core are demo-ready and run entirely on localhost. Remaining items are optional governance/UX refinements — no external infrastructure required.*
