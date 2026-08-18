# SkillMatch Nepal — Backend API

ML-based resume-to-job matching backend for IT graduates in Nepal.
Built with **Django 5 + Django REST Framework + PostgreSQL**, with a pluggable
matching engine (TF-IDF + cosine baseline today, Sentence-BERT later).

This is the API that powers the `skillmatch-frontend` Next.js app.

## Tech stack

| Layer            | Technology                                  |
|------------------|---------------------------------------------|
| Web framework    | Django 5, Django REST Framework             |
| Auth             | JWT (djangorestframework-simplejwt)         |
| Database         | PostgreSQL                                   |
| Resume parsing   | pdfminer.six (PDF), python-docx (DOCX)      |
| Skill extraction | Dictionary + word-boundary matching         |
| Matching engine  | scikit-learn (TF-IDF + cosine similarity)   |
| API docs         | drf-spectacular (Swagger UI)                |
| CORS             | django-cors-headers                         |

## Project structure

```
config/         Django project (settings, urls, wsgi/asgi)
accounts/       Custom email user, candidate/employer profiles, JWT auth
skills/         Skill vocabulary (shared across resumes & jobs)
resumes/        Resume upload, text parsing, skill extraction
jobs/           Job postings (employer CRUD, public listing)
applications/   Candidate applications (auto-scored on submit)
matching/       Pluggable matching engine + recommendation endpoints
common/         Shared DRF permissions
```

## Getting started

### 1. Create and activate a virtualenv
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env           # then edit DB credentials
```

### 3. Set up PostgreSQL

PostgreSQL is the **only** supported database. There is no SQLite fallback:
development, tests and evaluation all run on the same engine, so behaviour
verified locally is behaviour that holds in deployment.

```bash
psql -U postgres -c "CREATE DATABASE skillmatch;"
```

Then set the credentials in `.env`:

```ini
DB_NAME=skillmatch
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Migrate, seed, run
```bash
python manage.py migrate
python manage.py seed_synthetic     # or seed_demo for a small demo set
python manage.py createsuperuser    # optional, for the admin panel
python manage.py runserver
```

**Importing the existing SQLite dataset** (one-off, if you have `db.sqlite3`):
```bash
python manage.py migrate
python manage.py migrate_sqlite_to_postgres --sqlite db.sqlite3 --dry-run   # preview
python manage.py migrate_sqlite_to_postgres --sqlite db.sqlite3
```
Copies all application tables in foreign-key-safe order, converts SQLite's
integer booleans and text JSON to native Postgres types, and realigns every
sequence afterwards. Safe to re-run.

API runs at http://localhost:8000  ·  Swagger docs at http://localhost:8000/api/docs/

## Key endpoints

| Method | Endpoint                                  | Description                          |
|--------|-------------------------------------------|--------------------------------------|
| POST   | `/api/auth/register/`                     | Register (candidate or employer)     |
| POST   | `/api/auth/login/`                        | Obtain JWT access + refresh tokens   |
| POST   | `/api/auth/refresh/`                      | Refresh access token                 |
| GET    | `/api/auth/me/`                           | Current user + profile               |
| GET/PATCH | `/api/auth/profile/`                   | Read/update own profile              |
| GET    | `/api/skills/`                            | List skills                          |
| GET/POST | `/api/resumes/`                         | List / upload resumes (candidate)    |
| GET/POST | `/api/jobs/`                            | List (public) / create (employer)    |
| GET/POST | `/api/applications/`                    | List / apply to a job                |
| GET    | `/api/matching/recommendations/`          | Ranked job matches for candidate     |
| GET    | `/api/matching/jobs/<id>/candidates/`     | Ranked candidates for a job (owner)  |

## How matching works

`final_score = 0.6 * semantic_similarity + 0.4 * skill_overlap` (scaled to 0–100).

- **semantic_similarity** — cosine similarity of TF-IDF vectors of the resume text
  and the job text (`matching/engine/tfidf.py`).
- **skill_overlap** — fraction of the job's required skills found on the candidate.

The engine is pluggable: implement `BaseMatcher` and register it in
`matching/engine/factory.py`, then set `MATCHER_BACKEND=semantic` to swap in
Sentence-BERT without touching the rest of the code.

## Tests
```bash
python manage.py test                   # runs against PostgreSQL (test_skillmatch)
```
The database user needs `CREATEDB` to build the throwaway test database.
29 tests currently pass, covering matching, ranking order, score/explanation
consistency, upload validation, field validation, job visibility and
object-level access control.
