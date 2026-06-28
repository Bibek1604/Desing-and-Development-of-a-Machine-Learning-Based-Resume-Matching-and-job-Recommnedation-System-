"""
Seed a large synthetic dataset for load testing and ML evaluation.

    python manage.py seed_synthetic                 # ~30k+ rows (defaults)
    python manage.py seed_synthetic --candidates 5000 --jobs 2000

Row budget with defaults:
    300 skills + 12,000 candidates (+12,000 profiles) + 800 employers
    (+800 profiles) + 5,000 jobs + 9,000 applications + 3,000 notifications
    = ~42,900 rows (plus skill assignments).

Designed to be fast: bulk_create everywhere, one shared password hash,
signals are bypassed automatically because bulk_create does not emit them.
All accounts share the password "Password123!".
"""
from __future__ import annotations

import random

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

FIRST = [
    "Aarav", "Priya", "Bibek", "Sita", "Ramesh", "Anisha", "Sujan", "Maya",
    "Kiran", "Nisha", "Prakash", "Gita", "Suresh", "Rita", "Dipesh", "Mina",
    "Roshan", "Sarita", "Bikash", "Laxmi", "Nabin", "Puja", "Santosh", "Asha",
    "Rajesh", "Kabita", "Milan", "Sunita", "Deepak", "Pratima", "Saugat",
    "Ishwori", "Nirajan", "Bandana", "Pawan", "Srijana", "Umesh", "Alina",
]
LAST = [
    "Sharma", "Thapa", "Karki", "Shrestha", "Gurung", "Rai", "Tamang", "Magar",
    "Adhikari", "Poudel", "Khadka", "Basnet", "Joshi", "Bhattarai", "Koirala",
    "Regmi", "Dahal", "Subedi", "Pandey", "Acharya", "Ghimire", "Maharjan",
]
UNIVERSITIES = [
    "Tribhuvan University", "Kathmandu University", "Pokhara University",
    "Purbanchal University", "Softwarica College", "Islington College",
    "Herald College", "The British College", "NCIT", "Deerwalk Institute",
]
DEGREES = ["BSc IT", "BCA", "BSc CSIT", "BE Computer", "BIT", "BSc Computing", "BIM"]
DISTRICTS = ["Kathmandu", "Lalitpur", "Bhaktapur", "Pokhara", "Chitwan", "Butwal", "Biratnagar", "Dharan"]
COMPANIES = [
    "Fusemachines", "Leapfrog Technology", "CloudFactory", "Khalti", "F1Soft",
    "Cotiviti Nepal", "Verisk Nepal", "Deerwalk", "LogPoint", "Javra Software",
    "Insight Workshop", "EB Pearls", "YoungInnovations", "Sastodeal", "Daraz",
    "eSewa", "Gham Power", "Bottle Technology", "Code Himalaya", "TechKraft",
]
ROLES = [
    "Backend Developer", "Frontend Developer", "Full Stack Developer",
    "ML Engineer", "Data Analyst", "Data Engineer", "DevOps Engineer",
    "QA Engineer", "Mobile Developer", "UI/UX Designer", "Product Manager",
    "Database Administrator", "Cloud Engineer", "Security Analyst",
]
SKILL_NAMES = [
    "Python", "Django", "FastAPI", "Flask", "JavaScript", "TypeScript", "React",
    "Next.js", "Vue", "Angular", "Node.js", "Express", "Java", "Spring Boot",
    "Kotlin", "Swift", "Flutter", "Dart", "React Native", "PHP", "Laravel",
    "Go", "Rust", "C++", "C#", ".NET", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "Elasticsearch", "GraphQL", "REST API", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "Terraform", "Linux", "Git", "CI/CD", "Jenkins",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow",
    "PyTorch", "scikit-learn", "Pandas", "NumPy", "Data Visualization",
    "Tableau", "Power BI", "Excel", "Statistics", "A/B Testing", "Airflow",
    "Spark", "Kafka", "HTML", "CSS", "Tailwind", "Sass", "Figma", "Adobe XD",
    "Selenium", "Cypress", "Jest", "Pytest", "JUnit", "Agile", "Scrum", "Jira",
]
JOB_TITLE_PREFIX = ["Junior", "Mid-level", "Senior", "Lead", "Associate", "Trainee"]

rng = random.Random(42)


def _email(first: str, last: str, i: int, domain: str) -> str:
    return f"{first.lower()}.{last.lower()}{i}@{domain}"


class Command(BaseCommand):
    help = "Seed a large synthetic dataset (~30k+ rows by default)."

    def add_arguments(self, parser):
        parser.add_argument("--candidates",    type=int, default=12000)
        parser.add_argument("--employers",     type=int, default=800)
        parser.add_argument("--jobs",          type=int, default=5000)
        parser.add_argument("--applications",  type=int, default=9000)
        parser.add_argument("--notifications", type=int, default=3000)

    @transaction.atomic
    def handle(self, *args, **opts):
        from accounts.models import CandidateProfile, EmployerProfile, User
        from applications.models import Application
        from jobs.models import Job
        from notifications.models import Notification
        from skills.models import Skill

        n_cand, n_emp = opts["candidates"], opts["employers"]
        n_jobs, n_apps, n_notifs = opts["jobs"], opts["applications"], opts["notifications"]

        password = make_password("Password123!")  # hash once, reuse
        now = timezone.now()

        # ── Skills ────────────────────────────────────────────────────────────
        existing = set(Skill.objects.values_list("name", flat=True))
        skill_rows = []
        for name in SKILL_NAMES:
            if name not in existing:
                skill_rows.append(Skill(name=name, slug=name.lower().replace(" ", "-").replace(".", "").replace("#", "sharp").replace("+", "p"), category="technical"))
        # pad with versioned variants to reach ~300 skills
        for base in SKILL_NAMES:
            for suffix in ("Advanced", "Fundamentals", "Certification"):
                name = f"{base} {suffix}"
                if len(existing) + len(skill_rows) >= 300:
                    break
                if name not in existing:
                    skill_rows.append(Skill(name=name, slug=f"{base.lower().replace(' ', '-').replace('.', '').replace('#', 'sharp').replace('+', 'p')}-{suffix.lower()}", category="technical"))
        Skill.objects.bulk_create(skill_rows, ignore_conflicts=True)
        skills = list(Skill.objects.all())
        self.stdout.write(f"skills: {len(skills)} total")

        # ── Candidate users ───────────────────────────────────────────────────
        cand_users = []
        for i in range(n_cand):
            f, l = rng.choice(FIRST), rng.choice(LAST)
            cand_users.append(User(
                email=_email(f, l, i, "synthetic.skillmatch.test"),
                full_name=f"{f} {l}",
                role=User.Role.CANDIDATE,
                password=password,
                is_active=True,
            ))
        User.objects.bulk_create(cand_users, batch_size=2000, ignore_conflicts=True)
        cand_users = list(User.objects.filter(email__endswith="synthetic.skillmatch.test", role=User.Role.CANDIDATE))
        self.stdout.write(f"candidate users: {len(cand_users)}")

        # ── Candidate profiles ────────────────────────────────────────────────
        profiles = []
        for u in cand_users:
            role = rng.choice(ROLES)
            profiles.append(CandidateProfile(
                user=u,
                degree=rng.choice(DEGREES),
                university=rng.choice(UNIVERSITIES),
                district=rng.choice(DISTRICTS),
                graduation_year=rng.randint(2019, 2026),
                cgpa=round(rng.uniform(2.4, 4.0), 2),
                preferred_role=role,
                resume_summary=(
                    f"{rng.choice(DEGREES)} graduate focused on {role.lower()} work. "
                    f"Comfortable with {', '.join(rng.sample(SKILL_NAMES, 5))}."
                ),
                ats_score=rng.randint(35, 95),
                hiring_probability=round(rng.uniform(0.2, 0.95), 2),
                expected_salary_min=rng.randrange(25000, 60000, 5000),
                expected_salary_max=rng.randrange(60000, 160000, 5000),
            ))
        CandidateProfile.objects.bulk_create(profiles, batch_size=2000, ignore_conflicts=True)
        self.stdout.write(f"candidate profiles: {len(profiles)}")

        # skill assignments (6–10 per candidate) via the through table
        Through = CandidateProfile.skills.through
        assignments = []
        profile_ids = list(CandidateProfile.objects.filter(user__in=cand_users).values_list("id", flat=True))
        skill_ids = [s.id for s in skills]
        for pid in profile_ids:
            for sid in rng.sample(skill_ids, rng.randint(6, 10)):
                assignments.append(Through(candidateprofile_id=pid, skill_id=sid))
        Through.objects.bulk_create(assignments, batch_size=5000, ignore_conflicts=True)
        self.stdout.write(f"skill assignments: {len(assignments)}")

        # ── Employers ─────────────────────────────────────────────────────────
        emp_users = []
        for i in range(n_emp):
            f, l = rng.choice(FIRST), rng.choice(LAST)
            emp_users.append(User(
                email=_email(f, l, i, "employer.skillmatch.test"),
                full_name=f"{f} {l}",
                role=User.Role.EMPLOYER,
                password=password,
                is_active=True,
            ))
        User.objects.bulk_create(emp_users, batch_size=2000, ignore_conflicts=True)
        emp_users = list(User.objects.filter(email__endswith="employer.skillmatch.test"))
        EmployerProfile.objects.bulk_create(
            [EmployerProfile(user=u, company_name=rng.choice(COMPANIES), location="Kathmandu, Nepal") for u in emp_users],
            batch_size=2000, ignore_conflicts=True,
        )
        self.stdout.write(f"employers: {len(emp_users)}")

        # ── Jobs ──────────────────────────────────────────────────────────────
        job_rows = []
        for i in range(n_jobs):
            role = rng.choice(ROLES)
            title = f"{rng.choice(JOB_TITLE_PREFIX)} {role}"
            smin = rng.randrange(25000, 90000, 5000)
            req = rng.sample(SKILL_NAMES, rng.randint(4, 8))
            job_rows.append(Job(
                employer=rng.choice(emp_users),
                title=title,
                company=rng.choice(COMPANIES),
                description=(
                    f"We are hiring a {title.lower()} to join our team in Nepal. "
                    f"You will work with {', '.join(req[:3])} and collaborate with "
                    f"cross-functional teams to ship reliable product features."
                ),
                requirements=", ".join(req),
                location=rng.choice(DISTRICTS) + ", Nepal",
                job_type=rng.choice([c[0] for c in Job.JobType.choices]),
                salary_min=smin,
                salary_max=smin + rng.randrange(15000, 80000, 5000),
                is_active=rng.random() > 0.12,
            ))
        Job.objects.bulk_create(job_rows, batch_size=2000)
        jobs = list(Job.objects.filter(employer__in=emp_users))
        self.stdout.write(f"jobs: {len(jobs)}")

        # job required skills (3–6 each) — keep modest to bound row count
        JThrough = Job.required_skills.through
        j_assign = []
        for j in jobs:
            for sid in rng.sample(skill_ids, rng.randint(3, 6)):
                j_assign.append(JThrough(job_id=j.id, skill_id=sid))
        JThrough.objects.bulk_create(j_assign, batch_size=5000, ignore_conflicts=True)
        self.stdout.write(f"job skill links: {len(j_assign)}")

        # ── Applications (unique candidate+job pairs) ─────────────────────────
        pairs = set()
        app_rows = []
        while len(app_rows) < n_apps:
            c = rng.choice(cand_users); j = rng.choice(jobs)
            if (c.id, j.id) in pairs:
                continue
            pairs.add((c.id, j.id))
            app_rows.append(Application(
                candidate=c, job=j,
                status=rng.choices(
                    [Application.Status.APPLIED, Application.Status.REVIEWED,
                     Application.Status.SHORTLISTED, Application.Status.REJECTED],
                    weights=[55, 25, 12, 8],
                )[0],
                match_score=rng.randint(20, 96),
                cover_note="I believe my skills are a strong match for this role.",
            ))
        Application.objects.bulk_create(app_rows, batch_size=2000, ignore_conflicts=True)
        self.stdout.write(f"applications: {len(app_rows)}")

        # ── Notifications ─────────────────────────────────────────────────────
        notif_rows = []
        for _ in range(n_notifs):
            c = rng.choice(cand_users); j = rng.choice(jobs)
            score = rng.randint(55, 97)
            notif_rows.append(Notification(
                candidate=c, job=j,
                notification_type=(
                    Notification.Type.HIGH_PRIORITY if score >= 85 else Notification.Type.JOB_MATCH
                ),
                match_score=score,
                match_data={
                    "matched_skills": rng.sample(SKILL_NAMES, 4),
                    "missing_skills": rng.sample(SKILL_NAMES, 2),
                    "reasons": [f"Strong overlap on {rng.choice(SKILL_NAMES)}"],
                    "explanation_summary": "High semantic similarity with your profile.",
                },
                is_read=rng.random() > 0.6,
                sent_at=now,
            ))
        Notification.objects.bulk_create(notif_rows, batch_size=2000, ignore_conflicts=True)
        self.stdout.write(f"notifications: {len(notif_rows)}")

        total = (len(skills) + len(cand_users) + len(profiles) + len(emp_users) * 2
                 + len(jobs) + len(app_rows) + len(notif_rows))
        self.stdout.write(self.style.SUCCESS(
            f"Done. ~{total:,} primary rows (+{len(assignments) + len(j_assign):,} skill links). "
            "All synthetic accounts use password 'Password123!'."
        ))
