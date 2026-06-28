"""Import the Kathmandu IT-graduate CV Excel dataset into the database.

Reads  Kathmandu_IT_Graduate_CVs.xlsx  (12-column CV dataset) and creates:
  • Skill objects  (all unique skills found in the Technical Skills column)
  • User + CandidateProfile + Resume  (one per Excel row)

The Resume.raw_text is assembled from all CV fields so the TF-IDF /
semantic matching engine has rich, realistic content to score against.

Usage
-----
  # default — looks for the xlsx two levels above BASE_DIR (thesis root)
  python manage.py seed_from_excel

  # explicit path
  python manage.py seed_from_excel --file /path/to/Kathmandu_IT_Graduate_CVs.xlsx

  # limit rows (useful for quick smoke-tests)
  python manage.py seed_from_excel --limit 500

  # wipe previously-imported rows first, then re-import
  python manage.py seed_from_excel --clear
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from accounts.models import CandidateProfile
from resumes.models import Resume
from skills.models import Skill
from jobs.models import Job


def _require_pandas():
    try:
        import pandas as pd          # noqa: F401
        import openpyxl              # noqa: F401
    except ImportError:
        print(
            "pandas and openpyxl are required.\n"
            "Install them with:  pip install pandas openpyxl"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Resume text builder
# ---------------------------------------------------------------------------

def _build_resume_text(row: dict) -> str:
    """Construct a realistic plain-text resume from the 12 CV fields."""
    name        = row.get("Full Name", "")
    email       = row.get("Email", "")
    phone       = row.get("Phone", "")
    address     = row.get("Address", "")
    degree      = row.get("Degree", "")
    college     = row.get("College", "")
    university  = row.get("University", "")
    grad_year   = row.get("Graduation Year", "")
    cgpa        = row.get("CGPA", "")
    skills_raw  = row.get("Technical Skills", "")
    project     = row.get("Project (Title | Description)", "")
    internship  = row.get("Internship / Work Experience", "")

    # Split project into title + description if separated by " | "
    project_parts = str(project).split(" | ", 1)
    proj_title = project_parts[0].strip()
    proj_desc  = project_parts[1].strip() if len(project_parts) > 1 else ""

    lines = [
        f"{name}",
        f"{address}  |  {email}  |  {phone}",
        "",
        "EDUCATION",
        f"{degree}",
        f"{university} — {college}",
        f"Graduated: {grad_year}  |  CGPA: {cgpa} / 4.0",
        "",
        "TECHNICAL SKILLS",
        f"{skills_raw}",
        "",
        "FINAL YEAR PROJECT",
        f"{proj_title}",
        f"{proj_desc}",
        "",
        "INTERNSHIP / WORK EXPERIENCE",
        f"{internship}",
    ]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Skill normaliser — handle common variants
# ---------------------------------------------------------------------------
ALIASES = {
    "html/css": ["html", "css", "html5", "css3"],
    "rest apis": ["rest api", "restful api", "restful apis"],
    "node.js":  ["nodejs", "node js"],
    "next.js":  ["nextjs", "next js"],
    "react":    ["react.js", "reactjs"],
    "scikit-learn": ["sklearn", "scikit learn"],
}


def _normalise(raw: str) -> str:
    """Lowercase + strip; expand common aliases to canonical form."""
    s = raw.strip().lower()
    for canonical, variants in ALIASES.items():
        if s in variants:
            return canonical
    return s


def _parse_skills(skills_str: str) -> list[str]:
    """Return a list of raw (stripped) skill strings from a comma-separated cell."""
    if not skills_str or str(skills_str).strip() in ("nan", ""):
        return []
    parts = re.split(r",\s*", str(skills_str).strip())
    seen, result = set(), []
    for p in parts:
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            result.append(p)
    return result


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Import Kathmandu IT-graduate CV Excel data into the database."

    # Default xlsx path: two levels above BASE_DIR (= thesis root)
    _DEFAULT_XLSX = Path(settings.BASE_DIR).parent.parent / "Kathmandu_IT_Graduate_CVs.xlsx"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--file", default=str(self._DEFAULT_XLSX),
            help="Path to the CV Excel file (default: thesis root).",
        )
        parser.add_argument(
            "--limit", type=int, default=0,
            help="Maximum rows to import (0 = all).",
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete all previously-imported CV rows before re-importing.",
        )
        parser.add_argument(
            "--batch-size", type=int, default=200,
            help="Number of rows to commit per DB transaction (default 200).",
        )

    # ------------------------------------------------------------------
    def handle(self, *args, **options) -> None:
        _require_pandas()
        import pandas as pd

        xlsx_path = Path(options["file"])
        if not xlsx_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {xlsx_path}"))
            self.stderr.write("Pass the correct path with --file <path>")
            return

        self.stdout.write(f"Reading  {xlsx_path} …")
        df = pd.read_excel(xlsx_path, dtype=str)
        df = df.fillna("")

        if options["limit"] > 0:
            df = df.head(options["limit"])
        total = len(df)
        self.stdout.write(f"Rows to process: {total:,}")

        if options["clear"]:
            self._clear_imported()

        # ── 1. Collect all unique skills and bulk-create ──────────────
        skill_map = self._seed_skills(df)

        # ── 2. Import candidates in batches ──────────────────────────
        batch_size = options["batch_size"]
        imported = skipped = 0

        for batch_start in range(0, total, batch_size):
            batch = df.iloc[batch_start: batch_start + batch_size]
            b_imp, b_skip = self._import_batch(batch, skill_map)
            imported += b_imp
            skipped  += b_skip
            done = min(batch_start + batch_size, total)
            self.stdout.write(
                f"  {done:>6,} / {total:,}  "
                f"(imported {imported:,}, skipped {skipped:,})",
                ending="\r",
            )
            self.stdout.flush()

        self.stdout.write("")   # newline after \r
        self.stdout.write(self.style.SUCCESS(
            f"\nDone.  Imported: {imported:,}  |  Skipped (dup email): {skipped:,}"
        ))
        self.stdout.write(
            f"Total candidates in DB: "
            f"{CandidateProfile.objects.count():,}"
        )

    # ------------------------------------------------------------------
    def _clear_imported(self) -> None:
        """Remove users whose emails look like they came from the generated dataset."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "email.com"]
        qs = User.objects.filter(
            role=User.Role.CANDIDATE,
            email__regex=r"^[a-z]+[\.\-_]?[a-z]+\d*@",
        )
        count = qs.count()
        qs.delete()
        self.stdout.write(f"Cleared {count:,} previously-imported candidate rows.")

    # ------------------------------------------------------------------
    def _seed_skills(self, df) -> dict[str, Skill]:
        """Extract all unique skills from the dataframe and upsert them.

        Returns skill_map keyed by lowercase skill name.
        """
        # Collect raw (stripped) skill names
        raw_names: set[str] = set()
        for cell in df["Technical Skills"]:
            for s in _parse_skills(cell):
                raw_names.add(s)

        skill_map: dict[str, Skill] = {}
        for raw in raw_names:
            key = raw.lower()
            # 1. Try exact case-insensitive match first
            existing = Skill.objects.filter(name__iexact=raw).first()
            if existing:
                skill_map[key] = existing
                continue
            # 2. Create; handle slug collision gracefully
            try:
                obj = Skill.objects.create(name=raw, category="")
                skill_map[key] = obj
            except Exception:
                # Slug collision — find the row that owns this slug
                from django.utils.text import slugify
                slug = slugify(raw)
                obj = Skill.objects.filter(slug=slug).first()
                if obj:
                    skill_map[key] = obj

        self.stdout.write(self.style.SUCCESS(
            f"Skills in DB: {Skill.objects.count():,}  "
            f"(processed {len(skill_map):,} unique from Excel)"
        ))
        return skill_map

    # ------------------------------------------------------------------
    def _import_batch(self, batch, skill_map: dict[str, Skill]) -> tuple[int, int]:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        imported = skipped = 0

        with transaction.atomic():
            for _, row in batch.iterrows():
                email = str(row.get("Email", "")).strip().lower()
                if not email or User.objects.filter(email=email).exists():
                    skipped += 1
                    continue

                full_name   = str(row.get("Full Name", "")).strip()
                address     = str(row.get("Address", "")).strip()
                degree      = str(row.get("Degree", "")).strip()
                grad_year   = str(row.get("Graduation Year", "")).strip()
                skills_raw  = str(row.get("Technical Skills", "")).strip()
                internship  = str(row.get("Internship / Work Experience", "")).strip()

                headline = (
                    f"{degree} Graduate"
                    + (f" · {grad_year}" if grad_year else "")
                )

                # Create user (triggers post_save signal → profile auto-created)
                user = User.objects.create_user(
                    email=email,
                    password="changeme123",
                    full_name=full_name,
                    role=User.Role.CANDIDATE,
                )

                # Profile
                profile, _ = CandidateProfile.objects.get_or_create(user=user)
                profile.headline = headline
                profile.location = address

                cand_skills = [
                    skill_map[n.lower()]
                    for n in _parse_skills(skills_raw)
                    if n.lower() in skill_map
                ]
                profile.skills.set(cand_skills)
                profile.resume_score = min(50 + len(cand_skills) * 5, 100)
                profile.save(update_fields=["headline", "location", "resume_score"])

                # Resume with full constructed text
                raw_text = _build_resume_text(dict(row))
                resume, _ = Resume.objects.get_or_create(
                    candidate=user,
                    defaults={"original_filename": "resume.pdf", "is_primary": True},
                )
                resume.raw_text  = raw_text
                resume.is_primary = True
                resume.save(update_fields=["raw_text", "is_primary"])
                resume.extracted_skills.set(cand_skills)

                imported += 1

        return imported, skipped
