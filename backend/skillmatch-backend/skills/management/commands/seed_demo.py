"""Populate the database with demo skills, users, and jobs.

Mirrors the data shown in the Next.js frontend so the two line up during a demo.

Usage:  python manage.py seed_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from skills.models import Skill
from accounts.models import CandidateProfile, EmployerProfile
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
        "employer_email": "employer_fusemachines@demo.np",
        "logo_url": "https://github.com/fusemachines.png",
    },
    {
        "title": "Frontend Developer (React)", "company": "Leapfrog Technology",
        "location": "Lalitpur (On-site)", "job_type": "full_time",
        "salary_text": "NPR 50k - 80k / month",
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "REST APIs"],
        "description": "Build responsive, accessible interfaces for international clients using a modern React and TypeScript stack.",
        "employer_email": "employer_leapfrog@demo.np",
        "logo_url": "https://github.com/leapfrogtechnology.png",
    },
    {
        "title": "Data Analyst Intern", "company": "Khalti Digital Wallet",
        "location": "Kathmandu (On-site)", "job_type": "internship",
        "salary_text": "NPR 20k / month",
        "skills": ["SQL", "Python", "Excel", "Data Visualization"],
        "description": "Support the analytics team with reporting, dashboards, and exploratory analysis of payment data.",
        "employer_email": "employer_khalti@demo.np",
        "logo_url": "https://github.com/khalti.png",
    },
    {
        "title": "Backend Engineer (Django)", "company": "Cedar Gate Technologies",
        "location": "Kathmandu (Hybrid)", "job_type": "full_time",
        "salary_text": "NPR 70k - 110k / month",
        "skills": ["Python", "Django", "PostgreSQL", "Docker", "REST APIs"],
        "description": "Design and maintain scalable backend services and APIs powering healthcare data products.",
        "employer_email": "employer_cedargate@demo.np",
        "logo_url": "https://github.com/cedargate.png",
    },
    {
        "title": "Junior NLP Engineer", "company": "Docsumo",
        "location": "Remote (Nepal)", "job_type": "full_time",
        "salary_text": "NPR 65k - 95k / month",
        "skills": ["Python", "spaCy", "Transformers", "NER", "PyTorch"],
        "description": "Improve document-understanding models that extract structured data from unstructured documents.",
        "employer_email": "employer_docsumo@demo.np",
        "logo_url": "https://github.com/docsumo.png",
    },
    {
        "title": "Software Engineer, Machine Learning", "company": "Google",
        "location": "Mountain View, CA (Hybrid)", "job_type": "full_time",
        "salary_text": "$140k - $210k / year",
        "skills": ["Python", "TensorFlow", "PyTorch", "NLP", "scikit-learn"],
        "description": "Develop the next generation of machine learning models powering search, ads, and assistant technologies.",
        "employer_email": "employer_google@demo.np",
        "logo_url": "https://github.com/google.png",
    },
    {
        "title": "Cloud Solution Architect (Azure)", "company": "Microsoft",
        "location": "Redmond, WA (On-site)", "job_type": "full_time",
        "salary_text": "$130k - $190k / year",
        "skills": ["Docker", "CI/CD", "SQL", "Python", "REST APIs"],
        "description": "Help enterprise clients design and deploy scalable cloud infrastructures on Azure using modern DevOps practices.",
        "employer_email": "employer_microsoft@demo.np",
        "logo_url": "https://github.com/microsoft.png",
    },
    {
        "title": "Backend Engineer - AWS Database Services", "company": "Amazon",
        "location": "Seattle, WA (Hybrid)", "job_type": "full_time",
        "salary_text": "$135k - $195k / year",
        "skills": ["Python", "SQL", "PostgreSQL", "REST APIs", "Docker"],
        "description": "Build high-performance, fault-tolerant relational database engines powering critical AWS services.",
        "employer_email": "employer_amazon@demo.np",
        "logo_url": "https://github.com/amazon.png",
    },
    {
        "title": "Data Scientist, Product Analytics", "company": "Meta",
        "location": "Menlo Park, CA (Hybrid)", "job_type": "full_time",
        "salary_text": "$125k - $185k / year",
        "skills": ["Python", "SQL", "Pandas", "Data Visualization", "Excel"],
        "description": "Analyze petabyte-scale user interaction data to guide product strategy and improve core application metrics.",
        "employer_email": "employer_meta@demo.np",
        "logo_url": "https://github.com/facebook.png",
    },
    {
        "title": "Senior Frontend Engineer (UI Frameworks)", "company": "Netflix",
        "location": "Los Gatos, CA (Remote)", "job_type": "full_time",
        "salary_text": "$200k - $300k / year",
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "JavaScript"],
        "description": "Design and implement high-performance UI libraries used by the main streaming application across web platforms.",
        "employer_email": "employer_netflix@demo.np",
        "logo_url": "https://github.com/netflix.png",
    },
    {
        "title": "Software Engineer, Core Infrastructure", "company": "Uber",
        "location": "San Francisco, CA (Hybrid)", "job_type": "full_time",
        "salary_text": "$140k - $205k / year",
        "skills": ["Node.js", "REST APIs", "Docker", "CI/CD", "SQL"],
        "description": "Scale Uber's microservices mesh to support millions of concurrent rides and deliveries worldwide.",
        "employer_email": "employer_uber@demo.np",
        "logo_url": "https://github.com/uber.png",
    },
    {
        "title": "Full Stack Developer - Guest Booking", "company": "Airbnb",
        "location": "San Francisco, CA (Hybrid)", "job_type": "full_time",
        "salary_text": "$130k - $185k / year",
        "skills": ["React", "TypeScript", "Node.js", "REST APIs", "Tailwind CSS"],
        "description": "Build smooth and intuitive checkout interfaces, running high-frequency A/B experiments to maximize conversion.",
        "employer_email": "employer_airbnb@demo.np",
        "logo_url": "https://github.com/airbnb.png",
    },
    {
        "title": "Software Engineer - Payment APIs", "company": "Stripe",
        "location": "San Francisco, CA (Hybrid)", "job_type": "full_time",
        "salary_text": "$145k - $210k / year",
        "skills": ["Python", "REST APIs", "SQL", "PostgreSQL", "TypeScript"],
        "description": "Design clean and developer-friendly payment APIs that form the financial infrastructure of the internet.",
        "employer_email": "employer_stripe@demo.np",
        "logo_url": "https://github.com/stripe.png",
    },
    {
        "title": "Machine Learning Engineer - Personalization", "company": "Spotify",
        "location": "New York, NY (Hybrid)", "job_type": "full_time",
        "salary_text": "$130k - $180k / year",
        "skills": ["Python", "TensorFlow", "scikit-learn", "Pandas", "SQL"],
        "description": "Train and deploy deep recommendation models that power Discover Weekly and personalized music feeds.",
        "employer_email": "employer_spotify@demo.np",
        "logo_url": "https://github.com/spotify.png",
    },
    {
        "title": "DevOps Engineer - Actions Infrastructure", "company": "GitHub",
        "location": "Remote (Global)", "job_type": "full_time",
        "salary_text": "$120k - $175k / year",
        "skills": ["Docker", "CI/CD", "TypeScript", "REST APIs", "Node.js"],
        "description": "Maintain and scale the virtual environments running thousands of CI/CD jobs per second on GitHub Actions.",
        "employer_email": "employer_github@demo.np",
        "logo_url": "https://github.com/github.png",
    },
]


def download_logo(company_name, url):
    import os
    import ssl
    import urllib.request
    from django.conf import settings

    slug = company_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    filename = f"{slug}.png"
    logos_dir = os.path.join(settings.MEDIA_ROOT, "logos")
    os.makedirs(logos_dir, exist_ok=True)
    filepath = os.path.join(logos_dir, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return f"logos/{filename}"

    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            with open(filepath, "wb") as f:
                f.write(response.read())
        return f"logos/{filename}"
    except Exception as e:
        print(f"Failed to download logo for {company_name} from {url}: {e}")
        return ""


class Command(BaseCommand):
    help = "Seed demo skills, an employer with jobs, and a sample candidate."

    def handle(self, *args, **options):
        # Skills
        skill_map = {}
        for name, category in SKILLS:
            skill, _ = Skill.objects.get_or_create(name=name, defaults={"category": category})
            skill_map[name] = skill
        self.stdout.write(self.style.SUCCESS(f"Skills ready: {len(skill_map)}"))

        # Generic Employer (kept for compatibility)
        generic_employer, created = User.objects.get_or_create(
            email="employer@demo.np",
            defaults={"full_name": "Demo Employer", "role": User.Role.EMPLOYER},
        )
        if created:
            generic_employer.set_password("demopass123")
            generic_employer.save()

        # Build each company employer and job
        for spec in JOBS:
            # 1. Download logo
            logo_path = download_logo(spec["company"], spec["logo_url"])

            # 2. Employer user
            employer, created = User.objects.get_or_create(
                email=spec["employer_email"],
                defaults={"full_name": f"{spec['company']} Admin", "role": User.Role.EMPLOYER},
            )
            if created:
                employer.set_password("demopass123")
                employer.save()

            # 3. Employer profile with company name & logo
            profile, _ = EmployerProfile.objects.get_or_create(user=employer)
            profile.company_name = spec["company"]
            profile.location = spec["location"]
            if logo_path:
                profile.logo = logo_path
            profile.save()

            # 4. Job
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
        self.stdout.write("Login (generic employer): employer@demo.np / demopass123")
        self.stdout.write("Login (candidate):        candidate@demo.np / demopass123")
        for spec in JOBS:
            self.stdout.write(f"Login ({spec['company']}): {spec['employer_email']} / demopass123")


