"""Populate the database with demo skills, users, and jobs.

Mirrors the data shown in the Next.js frontend so the two line up during a demo.

Usage:  python manage.py seed_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from skills.models import Skill
from accounts.models import CandidateProfile
from jobs.models import Job

User = get_user_model()

SKILLS = [
    ("Python", "Language"), ("JavaScript", "Language"), ("TypeScript", "Language"),
    ("SQL", "Language"), ("React", "Frontend"), ("Next.js", "Frontend"),
    ("Tailwind CSS", "Frontend"), ("Django", "Backend"), ("Node.js", "Backend"),
    ("PostgreSQL", "Database"), ("Docker", "DevOps"), ("CI/CD", "DevOps"),
    ("TensorFlow", "ML"), ("PyTorch", "ML"), ("scikit-learn", "ML"),
    ("NLP", "ML"), ("spaCy", "ML"), ("Transformers", "ML"), ("NER", "ML"),
    ("Pandas", "Data"), ("Data Visualization", "Data"), ("Excel", "Data"),
    ("REST APIs", "Backend"), ("Selenium", "QA"), ("Jest", "QA"), ("Power BI", "Data"),
]

JOBS = [
    {
        "title": "Junior Machine Learning Engineer", "company": "Fusemachines",
        "location": "Kathmandu (Hybrid)", "job_type": "full_time",
        "salary_text": "NPR 60k - 90k / month",
        "skills": ["Python", "TensorFlow", "scikit-learn", "NLP", "Pandas"],
        "description": "Work on real-world ML pipelines, from data preprocessing to model deployment, alongside a senior research team.",
    },
    {
        "title": "Frontend Developer (React)", "company": "Leapfrog Technology",
        "location": "Lalitpur (On-site)", "job_type": "full_time",
        "salary_text": "NPR 50k - 80k / month",
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "REST APIs"],
        "description": "Build responsive, accessible interfaces for international clients using a modern React and TypeScript stack.",
    },
    {
        "title": "Data Analyst Intern", "company": "Khalti Digital Wallet",
        "location": "Kathmandu (On-site)", "job_type": "internship",
        "salary_text": "NPR 20k / month",
        "skills": ["SQL", "Python", "Excel", "Data Visualization"],
        "description": "Support the analytics team with reporting, dashboards, and exploratory analysis of payment data.",
    },
    {
        "title": "Backend Engineer (Django)", "company": "Cedar Gate Technologies",
        "location": "Kathmandu (Hybrid)", "job_type": "full_time",
        "salary_text": "NPR 70k - 110k / month",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "REST APIs"],
        "description": "Design and maintain scalable backend services and APIs powering healthcare data products.",
    },
    {
        "title": "Junior NLP Engineer", "company": "Docsumo",
        "location": "Remote (Nepal)", "job_type": "full_time",
        "salary_text": "NPR 65k - 95k / month",
        "skills": ["Python", "spaCy", "Transformers", "NER", "PyTorch"],
        "description": "Improve document-understanding models that extract structured data from unstructured documents.",
    },
]


class Command(BaseCommand):
    help = "Seed demo skills, an employer with jobs, and a sample candidate."

    def handle(self, *args, **options):
        # Skills
        skill_map = {}
        for name, category in SKILLS:
            skill, _ = Skill.objects.get_or_create(name=name, defaults={"category": category})
            skill_map[name] = skill
        self.stdout.write(self.style.SUCCESS(f"Skills ready: {len(skill_map)}"))

        # Employer + jobs
        employer, created = User.objects.get_or_create(
            email="employer@demo.np",
            defaults={"full_name": "Demo Employer", "role": User.Role.EMPLOYER},
        )
        if created:
            employer.set_password("demopass123")
            employer.save()
        for spec in JOBS:
            job, made = Job.objects.get_or_create(
                title=spec["title"], employer=employer,
                defaults={
                    "company": spec["company"], "location": spec["location"],
                    "job_type": spec["job_type"], "salary_text": spec["salary_text"],
                    "description": spec["description"],
                },
            )
            if made:
                job.required_skills.set(skill_map[s] for s in spec["skills"])
        self.stdout.write(self.style.SUCCESS(f"Jobs ready: {Job.objects.count()}"))

        # Candidate with a skill profile + resume text
        candidate, created = User.objects.get_or_create(
            email="candidate@demo.np",
            defaults={"full_name": "Aarav Sharma", "role": User.Role.CANDIDATE},
        )
        if created:
            candidate.set_password("demopass123")
            candidate.save()
        profile, _ = CandidateProfile.objects.get_or_create(user=candidate)
        profile.headline = "IT Graduate - Aspiring ML Engineer"
        profile.location = "Kathmandu, Nepal"
        cand_skills = ["Python", "TensorFlow", "NLP", "scikit-learn", "SQL", "Pandas"]
        profile.skills.set(skill_map[s] for s in cand_skills)
        profile.save()

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write("Login (employer):  employer@demo.np / demopass123")
        self.stdout.write("Login (candidate): candidate@demo.np / demopass123")
