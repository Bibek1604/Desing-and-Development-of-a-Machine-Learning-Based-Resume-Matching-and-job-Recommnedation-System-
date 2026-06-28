"""Bulk-import the 38-column synthetic CV dataset (Synthetic_IT_CVs_105k_38col.xlsx).

Designed for 100k+ rows: it uses one pre-computed password hash for every
synthetic account (no per-row bcrypt), batched ``bulk_create`` for Users,
CandidateProfiles and Resumes, a cached Skill vocabulary, and a single bulk
insert into the skills M2M through-table per batch.

Usage
-----
  # quick smoke test (recommended first)
  python manage.py seed_dataset_v3 --limit 1000

  # full load (slow on SQLite — expect several minutes and a large DB)
  python manage.py seed_dataset_v3 --file "../../Synthetic_IT_CVs_105k_38col.xlsx"

  # wipe previously-imported synthetic rows first
  python manage.py seed_dataset_v3 --clear --limit 5000

After loading, refresh the matcher index implicitly (it rebuilds on demand) and
optionally train the ranking model with:  python manage.py train_ranker
"""
from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils.text import slugify

from accounts.models import User, CandidateProfile
from resumes.models import Resume
from skills.models import Skill

AVAILABILITY_MAP = {
    "immediate": "immediate", "2 weeks": "2_weeks", "1 month": "1_month",
    "3 months": "3_months", "6 months": "6_months",
}
DEFAULT_FILE = "Synthetic_IT_CVs_105k_38col.xlsx"


def _num(text) -> int | None:
    digits = re.sub(r"[^0-9]", "", str(text or ""))
    return int(digits) if digits else None


def _rows_from_xlsx(path: Path, limit: int | None):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() for h in next(it)]
    for i, row in enumerate(it):
        if limit and i >= limit:
            break
        yield dict(zip(header, row))
    wb.close()


def _build_resume_text(r: dict) -> str:
    parts = [
        r.get("Full Name", ""), r.get("Resume Summary", ""), r.get("Career Objective", ""),
        f"Role: {r.get('Preferred Job Role','')} ({r.get('Role Category','')}, {r.get('Seniority Level','')})",
        f"{r.get('Years of Experience','')} years experience",
        f"Education: {r.get('Degree','')}, {r.get('College','')}, {r.get('University','')} ({r.get('Graduation Year','')}), CGPA {r.get('CGPA','')}",
        f"Technical Skills: {r.get('Technical Skills','')}",
        f"Soft Skills: {r.get('Soft Skills','')}",
        f"Certifications: {r.get('Certifications','')}",
        f"Primary Stack: {r.get('Primary Tech Stack','')}",
        f"Projects: {r.get('Projects','')}",
        f"Internship: {r.get('Internship Experience','')}",
        f"Work Experience: {r.get('Work Experience','')}",
        f"Languages: {r.get('Languages','')}",
        f"Preferred company type: {r.get('Company Type','')}; Work mode: {r.get('Work Mode','')}; English: {r.get('English Proficiency','')}",
        r.get("Achievement History", ""), r.get("Volunteer Experience", ""), r.get("Research Experience", ""),
    ]
    return "\n".join(p for p in parts if p and str(p) != "None")


class Command(BaseCommand):
    help = "Bulk-import the 38-column synthetic CV dataset for matching + training."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--file", type=str, default=None)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--batch", type=int, default=2000)
        parser.add_argument("--clear", action="store_true",
                            help="Delete previously-imported synthetic candidates first.")

    def handle(self, *args, **opts):
        path = Path(opts["file"]) if opts["file"] else Path(settings.BASE_DIR).parent.parent / DEFAULT_FILE
        if not path.exists():
            self.stderr.write(f"Dataset not found: {path}")
            return

        if opts["clear"]:
            n, _ = User.objects.filter(email__startswith="cv+").delete()
            self.stdout.write(f"Cleared {n} previously-imported rows.")

        pw = make_password("Passw0rd!demo")           # hashed ONCE, reused for all
        skill_cache = {s.name.lower(): s for s in Skill.objects.all()}
        Through = CandidateProfile.skills.through

        total = 0
        batch: list[dict] = []

        def flush(rows: list[dict]):
            nonlocal total
            # 1. Skills — create any not yet seen, in one go.
            new_names = {}
            for r in rows:
                for raw in str(r.get("Technical Skills", "") or "").split(","):
                    name = raw.strip()
                    key = name.lower()
                    if name and key not in skill_cache and key not in new_names:
                        new_names[key] = Skill(name=name, slug=slugify(name)[:60] or key[:60])
            if new_names:
                Skill.objects.bulk_create(list(new_names.values()), ignore_conflicts=True)
                for s in Skill.objects.filter(name__in=[s.name for s in new_names.values()]):
                    skill_cache[s.name.lower()] = s

            # 2. Users
            users = []
            for idx, r in enumerate(rows):
                gi = total + idx
                users.append(User(
                    email=f"cv+{gi}@dataset.local",
                    full_name=str(r.get("Full Name", "") or ""),
                    role=User.Role.CANDIDATE, password=pw, is_active=True,
                ))
            User.objects.bulk_create(users, batch_size=1000)

            # 3. Profiles + resumes (users now have PKs on SQLite)
            profiles, resumes, m2m = [], [], []
            for u, r in zip(users, rows):
                avail = AVAILABILITY_MAP.get(str(r.get("Availability", "")).strip().lower(), "")
                sal = _num(r.get("Expected Salary"))
                profiles.append(CandidateProfile(
                    user=u,
                    phone=str(r.get("Phone", "") or "")[:30],
                    location=str(r.get("Address", "") or "")[:120],
                    district=str(r.get("District", "") or "")[:80],
                    province=str(r.get("Province", "") or "")[:80],
                    degree=str(r.get("Degree", "") or "")[:100],
                    college=str(r.get("College", "") or "")[:160],
                    university=str(r.get("University", "") or "")[:160],
                    graduation_year=_num(r.get("Graduation Year")),
                    cgpa=(r.get("CGPA") or None),
                    soft_skills=str(r.get("Soft Skills", "") or ""),
                    certifications=str(r.get("Certifications", "") or ""),
                    languages=str(r.get("Languages", "") or ""),
                    github_url=_url(r.get("GitHub")), linkedin_url=_url(r.get("LinkedIn")),
                    portfolio_url=_url(r.get("Portfolio")),
                    resume_summary=str(r.get("Resume Summary", "") or ""),
                    career_objective=str(r.get("Career Objective", "") or ""),
                    preferred_role=str(r.get("Preferred Job Role", "") or "")[:120],
                    expected_salary_min=sal, expected_salary_max=int(sal * 1.3) if sal else None,
                    availability=avail,
                    industry_interest=str(r.get("Industry Interest", "") or "")[:120],
                    achievement_history=str(r.get("Achievement History", "") or ""),
                    volunteer_experience=str(r.get("Volunteer Experience", "") or ""),
                    research_experience=str(r.get("Research Experience", "") or ""),
                ))
            CandidateProfile.objects.bulk_create(profiles, batch_size=1000)

            for u, p, r in zip(users, profiles, rows):
                resumes.append(Resume(candidate=u, original_filename=f"cv_{u.pk}.txt",
                                      raw_text=_build_resume_text(r), is_primary=True))
                for raw in str(r.get("Technical Skills", "") or "").split(","):
                    s = skill_cache.get(raw.strip().lower())
                    if s:
                        m2m.append(Through(candidateprofile_id=p.pk, skill_id=s.pk))
            Resume.objects.bulk_create(resumes, batch_size=1000)
            Through.objects.bulk_create(m2m, batch_size=2000, ignore_conflicts=True)

            total += len(rows)
            self.stdout.write(f"  …{total} candidates imported")

        with transaction.atomic():
            for r in _rows_from_xlsx(path, opts["limit"]):
                batch.append(r)
                if len(batch) >= opts["batch"]:
                    flush(batch); batch = []
            if batch:
                flush(batch)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Imported {total} candidates with {len(skill_cache)} distinct skills."
        ))


def _url(v) -> str:
    s = str(v or "").strip()
    if not s or s == "None":
        return ""
    return s if s.startswith("http") else f"https://{s}"
