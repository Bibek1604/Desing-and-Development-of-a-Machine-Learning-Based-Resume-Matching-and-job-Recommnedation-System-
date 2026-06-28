"""Realistic seed data for the SkillMatch Nepal matching engine.

Populates the database with:
  - 38 IT skills common in the Kathmandu job market
  - 10 fresh IT-graduate candidates from Kathmandu universities
  - 10 job postings from real Kathmandu-based companies
  - Realistic resume text for each candidate so the TF-IDF / semantic
    engine has meaningful content to train and score against

Usage:
    python manage.py seed_realistic
    python manage.py seed_realistic --clear    # wipe existing demo data first
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

from accounts.models import CandidateProfile
from resumes.models import Resume
from skills.models import Skill
from jobs.models import Job

User = get_user_model()

# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
SKILLS = [
    ("Python",             "Language"),
    ("JavaScript",         "Language"),
    ("TypeScript",         "Language"),
    ("Java",               "Language"),
    ("PHP",                "Language"),
    ("SQL",                "Language"),
    ("React",              "Frontend"),
    ("Next.js",            "Frontend"),
    ("Tailwind CSS",       "Frontend"),
    ("Bootstrap",          "Frontend"),
    ("Django",             "Backend"),
    ("Flask",              "Backend"),
    ("Laravel",            "Backend"),
    ("Node.js",            "Backend"),
    ("Express.js",         "Backend"),
    ("REST APIs",          "Backend"),
    ("PostgreSQL",         "Database"),
    ("MySQL",              "Database"),
    ("MongoDB",            "Database"),
    ("Firebase",           "Database"),
    ("Docker",             "DevOps"),
    ("CI/CD",              "DevOps"),
    ("Linux",              "DevOps"),
    ("TensorFlow",         "ML"),
    ("scikit-learn",       "ML"),
    ("NLP",                "ML"),
    ("spaCy",              "ML"),
    ("Pandas",             "Data"),
    ("NumPy",              "Data"),
    ("Power BI",           "Data"),
    ("Data Visualization", "Data"),
    ("Excel",              "Data"),
    ("Android",            "Mobile"),
    ("Kotlin",             "Mobile"),
    ("Selenium",           "QA"),
    ("Jest",               "QA"),
    ("Postman",            "QA"),
    ("Git",                "DevOps"),
]

# ---------------------------------------------------------------------------
# Candidates — 10 fresh IT graduates from Kathmandu
# ---------------------------------------------------------------------------
CANDIDATES = [
    {
        "email":     "aarav.sharma@email.com",
        "password":  "pass1234",
        "full_name": "Aarav Sharma",
        "headline":  "BSc CSIT Graduate · Aspiring ML Engineer",
        "location":  "Kathmandu, Nepal",
        "skills":    ["Python", "scikit-learn", "TensorFlow", "NLP",
                      "Pandas", "SQL", "Git"],
        "resume_text": (
            "Aarav Sharma\n"
            "Kathmandu, Nepal | aarav.sharma@email.com\n\n"
            "EDUCATION\n"
            "BSc CSIT — Tribhuvan University, Kathmandu Model College, 2025. CGPA 3.4/4.0\n\n"
            "SKILLS\n"
            "Python, SQL, scikit-learn, TensorFlow, Keras, Pandas, NumPy, Matplotlib, "
            "NLP, spaCy, NLTK, TF-IDF, word embeddings, Git, GitHub, Jupyter, Linux.\n\n"
            "FINAL YEAR PROJECT\n"
            "ML-Based Resume-to-Job Matching System for IT Graduates in Nepal.\n"
            "Built an NLP pipeline that parses PDF resumes, extracts skills using a "
            "hybrid dictionary + spaCy NER approach, and ranks job postings by cosine "
            "similarity on TF-IDF and Sentence-BERT embeddings. "
            "Achieved 88% precision on 200 manually labelled resume-job pairs. "
            "Stack: Django REST Framework, React, PostgreSQL, Docker.\n\n"
            "MINOR PROJECT\n"
            "Sentiment Analysis of Nepali Social Media Posts — fine-tuned multilingual "
            "BERT on a Nepali Twitter dataset; 78% accuracy on 3-class classification.\n\n"
            "INTERNSHIP\n"
            "Data Analytics Intern, Fusemachines Nepal (3 months, 2024). "
            "Cleaned datasets with Pandas/NumPy, built Matplotlib visualisations, "
            "assisted in labelling NER training data.\n\n"
            "ACHIEVEMENTS\n"
            "Top 5% of BSc CSIT cohort 2025. "
            "DeepLearning.AI Machine Learning Specialisation (Coursera)."
        ),
    },
    {
        "email":     "priya.karki@email.com",
        "password":  "pass1234",
        "full_name": "Priya Karki",
        "headline":  "BIT Graduate · Frontend Developer",
        "location":  "Lalitpur, Nepal",
        "skills":    ["React", "JavaScript", "TypeScript", "Next.js",
                      "Tailwind CSS", "REST APIs", "Git"],
        "resume_text": (
            "Priya Karki\n"
            "Lalitpur, Nepal | priya.karki@email.com\n\n"
            "EDUCATION\n"
            "BIT — Pokhara University, Ncit College Lalitpur, 2025. CGPA 3.6/4.0\n\n"
            "SKILLS\n"
            "JavaScript, TypeScript, HTML5, CSS3, React.js, Next.js, Tailwind CSS, "
            "Bootstrap, Redux Toolkit, REST APIs, Postman, Git, Figma, npm.\n\n"
            "FINAL YEAR PROJECT\n"
            "NepalBazar — E-Commerce Platform for Local Handicraft Sellers. "
            "Next.js 14 + TypeScript + Tailwind CSS storefront integrated with a "
            "Django REST Framework backend. JWT auth, product search, real-time cart. "
            "Deployed on Vercel and Railway.\n\n"
            "MINOR PROJECT\n"
            "COVID-19 Dashboard Nepal — Chart.js + React visualisation of MoHP data "
            "with district-level choropleth maps.\n\n"
            "INTERNSHIP\n"
            "Frontend Developer Intern, Leapfrog Technology (4 months, 2024). "
            "Built reusable React component library with Storybook, collaborated on "
            "Figma design reviews, wrote Jest + React Testing Library tests.\n\n"
            "ACHIEVEMENTS\n"
            "Winner HackForNepal 2024 (Best UI/UX). "
            "Meta Front-End Developer Professional Certificate (Coursera, 2024)."
        ),
    },
    {
        "email":     "bibek.thapa@email.com",
        "password":  "pass1234",
        "full_name": "Bibek Thapa",
        "headline":  "BE Computer Engineering Graduate · Backend Developer",
        "location":  "Kathmandu, Nepal",
        "skills":    ["Python", "Django", "PostgreSQL", "Docker",
                      "REST APIs", "Linux", "Git", "SQL"],
        "resume_text": (
            "Bibek Thapa\n"
            "Kathmandu, Nepal | bibek.thapa@email.com\n\n"
            "EDUCATION\n"
            "BE Computer Engineering — Tribhuvan University, Nepal Engineering College "
            "(NEC) Bhaktapur, 2025. CGPA 3.3/4.0\n\n"
            "SKILLS\n"
            "Python, SQL, Django, Django REST Framework, Flask, PostgreSQL, MySQL, "
            "Redis (basics), Docker, Docker Compose, Nginx, Git, GitHub, Linux, Postman.\n\n"
            "FINAL YEAR PROJECT\n"
            "Saathi — Inventory and Billing System for Small Nepali Businesses. "
            "Django REST API + PostgreSQL covering products, stock, invoices, multi-user "
            "roles. Containerised with Docker Compose + Nginx. "
            "45 unit/integration tests, 87% code coverage. "
            "Used by a local hardware shop in Boudha during pilot testing.\n\n"
            "MINOR PROJECT\n"
            "Bus Route Finder REST API for Kathmandu Valley — "
            "models routes, stops, timetables in PostgreSQL; BFS shortest-path search. "
            "Documented with drf-spectacular (Swagger).\n\n"
            "INTERNSHIP\n"
            "Backend Developer Intern, Deerwalk Services (3 months, 2024). "
            "Maintained Django healthcare APIs, wrote migrations, optimised slow queries "
            "with EXPLAIN ANALYZE, participated in agile sprints.\n\n"
            "ACHIEVEMENTS\n"
            "IOE entrance distinction 2021. "
            "Django for Everybody — Coursera, University of Michigan."
        ),
    },
    {
        "email":     "sneha.gurung@email.com",
        "password":  "pass1234",
        "full_name": "Sneha Gurung",
        "headline":  "BSc CSIT Graduate · Data Analyst",
        "location":  "Kathmandu, Nepal",
        "skills":    ["SQL", "Python", "Excel", "Power BI", "Data Visualization",
                      "Pandas", "NumPy", "Git"],
        "resume_text": (
            "Sneha Gurung\n"
            "Kathmandu, Nepal | sneha.gurung@email.com\n\n"
            "EDUCATION\n"
            "BSc CSIT — Tribhuvan University, St. Xavier's College Maitighar, 2025. "
            "CGPA 3.5/4.0\n\n"
            "SKILLS\n"
            "Python (Pandas, NumPy, Matplotlib, Seaborn), SQL (PostgreSQL, MySQL), "
            "Power BI, Excel (pivot tables, VLOOKUP, macros), statistics, "
            "hypothesis testing, regression, Git, Jupyter Notebook, Google Colab.\n\n"
            "FINAL YEAR PROJECT\n"
            "Sales Performance Analytics Dashboard for a Kathmandu Retail Chain. "
            "Cleaned 3 years of POS data from MySQL using Pandas; built an interactive "
            "Power BI dashboard tracking revenue, top SKUs, and seasonal trends across "
            "5 outlets. Identified a 22% Q3 revenue dip; recommendations adopted.\n\n"
            "MINOR PROJECT\n"
            "Academic Performance Predictor — scikit-learn (Linear Regression, "
            "Random Forest) to predict CGPA from attendance and assignment scores. "
            "Feature importance visualisation.\n\n"
            "ACHIEVEMENTS\n"
            "St. Xavier's Merit Scholarship 2022 & 2023. "
            "Microsoft Certified: Power BI Data Analyst Associate (2025)."
        ),
    },
    {
        "email":     "rohan.shrestha@email.com",
        "password":  "pass1234",
        "full_name": "Rohan Shrestha",
        "headline":  "BIT Graduate · Full-Stack JavaScript Developer",
        "location":  "Kathmandu, Nepal",
        "skills":    ["JavaScript", "Node.js", "React", "Express.js",
                      "MongoDB", "REST APIs", "Git"],
        "resume_text": (
            "Rohan Shrestha\n"
            "Kathmandu, Nepal | rohan.shrestha@email.com\n\n"
            "EDUCATION\n"
            "BIT — Pokhara University, Islington College Kamaladi, 2025. "
            "CGPA 3.2/4.0 (London Metropolitan University affiliation)\n\n"
            "SKILLS\n"
            "JavaScript (ES6+), React.js, HTML5, CSS3, Bootstrap, "
            "Node.js, Express.js, MongoDB (Mongoose), MySQL, Axios, "
            "socket.io, REST APIs, JWT, Git, Postman, npm.\n\n"
            "FINAL YEAR PROJECT\n"
            "Khana Ghar — Food Ordering Web App for Kathmandu Restaurants. "
            "MERN stack (MongoDB, Express, React, Node). Role-based access for "
            "customers, restaurants, and delivery riders. "
            "eSewa sandbox payment API integrated. "
            "socket.io real-time order status notifications.\n\n"
            "MINOR PROJECT\n"
            "Real-time Chat App — socket.io + Node.js, MongoDB message persistence, "
            "mobile-friendly React UI.\n\n"
            "INTERNSHIP\n"
            "Junior Developer Intern, Yomari Inc. (2 months, 2024). "
            "Built REST endpoints in Node.js/Express, wrote Mongoose schemas.\n\n"
            "ACHIEVEMENTS\n"
            "3 personal GitHub projects, 120+ combined stars. "
            "AWS Cloud Practitioner Essentials (AWS Skill Builder, 2025)."
        ),
    },
    {
        "email":     "anisha.tamang@email.com",
        "password":  "pass1234",
        "full_name": "Anisha Tamang",
        "headline":  "BSc CSIT Graduate · Android / Mobile Developer",
        "location":  "Bhaktapur, Nepal",
        "skills":    ["Java", "Android", "Kotlin", "Firebase",
                      "MySQL", "REST APIs", "Git"],
        "resume_text": (
            "Anisha Tamang\n"
            "Bhaktapur, Nepal | anisha.tamang@email.com\n\n"
            "EDUCATION\n"
            "BSc CSIT — Tribhuvan University, Himalayan Whitehouse International "
            "College New Baneshwor, 2025. CGPA 3.3/4.0\n\n"
            "SKILLS\n"
            "Android SDK, Java, Kotlin, Jetpack (ViewModel, LiveData, Room), "
            "Retrofit, OkHttp, Firebase (Auth, Firestore, FCM), SQLite, MySQL, "
            "REST APIs, Android Studio, Figma, Git, Postman.\n\n"
            "FINAL YEAR PROJECT\n"
            "Swastha Jeevan — Personal Health Tracker Android App. "
            "Kotlin + Jetpack: steps, water, sleep, medication reminders. "
            "Room local storage + Firestore sync. Firebase Cloud Messaging push "
            "notifications. Published on Google Play Store (internal testing).\n\n"
            "MINOR PROJECT\n"
            "Kathmandu Bus Tracker — Android app showing bus location on Google Maps; "
            "consumed Flask REST API for route and schedule data.\n\n"
            "INTERNSHIP\n"
            "Android Developer Intern, CloudFactory Nepal (3 months, 2024). "
            "Labelled mobile UI datasets for ML pipelines; built internal Android "
            "utility app for the QA team.\n\n"
            "ACHIEVEMENTS\n"
            "Google Developer Student Club (GDSC) lead, Himalayan Whitehouse 2023-24."
        ),
    },
    {
        "email":     "dipesh.maharjan@email.com",
        "password":  "pass1234",
        "full_name": "Dipesh Maharjan",
        "headline":  "BE Computer Engineering Graduate · DevOps & Backend",
        "location":  "Lalitpur, Nepal",
        "skills":    ["Python", "Docker", "Linux", "Git", "CI/CD",
                      "PostgreSQL", "Flask", "REST APIs"],
        "resume_text": (
            "Dipesh Maharjan\n"
            "Lalitpur, Nepal | dipesh.maharjan@email.com\n\n"
            "EDUCATION\n"
            "BE Computer Engineering — Kathmandu University, School of Engineering "
            "Dhulikhel, 2025. CGPA 3.4/4.0\n\n"
            "SKILLS\n"
            "Python, Bash, SQL, Flask, FastAPI (basics), Django (basics), "
            "Docker, Docker Compose, GitHub Actions, Nginx, Linux (Ubuntu/CentOS), "
            "PostgreSQL, Redis, Git, Postman, systemd, htop.\n\n"
            "FINAL YEAR PROJECT\n"
            "Automated CI/CD Pipeline for a Flask Microservice. "
            "Docker Compose with Flask API, PostgreSQL, Redis, Nginx. "
            "GitHub Actions for lint (flake8), unit tests, build, and deploy. "
            "Reduced deployment time from 30 min to under 3 min.\n\n"
            "MINOR PROJECT\n"
            "System Resource Monitor CLI — Python (psutil + Rich) displaying live "
            "CPU, RAM, disk, and network I/O; JSON log export.\n\n"
            "INTERNSHIP\n"
            "Junior Systems Engineer Intern, Cotiviti Nepal (3 months, 2024). "
            "Managed Ubuntu 22.04 servers, cron jobs, log rotation; wrote Bash "
            "automation scripts; assisted Docker image builds and registry pushes.\n\n"
            "ACHIEVEMENTS\n"
            "Ranked 4th in KU Computer Engineering batch 2025. "
            "Linux Foundation: Introduction to Linux LFS101 (edX)."
        ),
    },
    {
        "email":     "srijana.rai@email.com",
        "password":  "pass1234",
        "full_name": "Srijana Rai",
        "headline":  "BIT Graduate · QA / Test Automation Engineer",
        "location":  "Kathmandu, Nepal",
        "skills":    ["Python", "Selenium", "Jest", "Postman",
                      "SQL", "Git", "REST APIs"],
        "resume_text": (
            "Srijana Rai\n"
            "Kathmandu, Nepal | srijana.rai@email.com\n\n"
            "EDUCATION\n"
            "BIT — Pokhara University, Softwarica College Dillibazar, 2025. "
            "CGPA 3.1/4.0 (Coventry University affiliation)\n\n"
            "SKILLS\n"
            "Manual testing (functional, regression, smoke, exploratory), "
            "Selenium WebDriver Python, pytest, Playwright (basics), "
            "Postman, Newman, Jest, React Testing Library, "
            "SQL (MySQL, PostgreSQL), Git, GitHub, JIRA, Chrome DevTools.\n\n"
            "FINAL YEAR PROJECT\n"
            "Automated Test Suite for an E-Commerce Web Application. "
            "80+ Selenium + pytest test cases covering login, cart, checkout, admin. "
            "GitHub Actions pipeline running tests on every PR. "
            "Identified 14 bugs; 11 fixed before submission. "
            "Produced test plan, test cases, and defect report.\n\n"
            "MINOR PROJECT\n"
            "Postman API Test Collection — 60 requests for a student management REST API "
            "including auth, CRUD, edge cases. Newman CI HTML reports.\n\n"
            "INTERNSHIP\n"
            "QA Intern, Verisk Nepal (3 months, 2024). "
            "Manual regression test cycles, JIRA Xray test case management, "
            "data-setup SQL scripts for the automation team.\n\n"
            "ACHIEVEMENTS\n"
            "ISTQB Foundation Level (CTFL) certified, 2025."
        ),
    },
    {
        "email":     "sujan.adhikari@email.com",
        "password":  "pass1234",
        "full_name": "Sujan Adhikari",
        "headline":  "BSc CSIT Graduate · PHP / Full-Stack Web Developer",
        "location":  "Kathmandu, Nepal",
        "skills":    ["PHP", "Laravel", "MySQL", "JavaScript",
                      "Bootstrap", "Git", "REST APIs"],
        "resume_text": (
            "Sujan Adhikari\n"
            "Kathmandu, Nepal | sujan.adhikari@email.com\n\n"
            "EDUCATION\n"
            "BSc CSIT — Tribhuvan University, Prime College Naya Baneshwor, 2025. "
            "CGPA 3.0/4.0\n\n"
            "SKILLS\n"
            "PHP 8, Laravel 10, Composer, Artisan CLI, Eloquent ORM, "
            "JavaScript (ES6+), Bootstrap 5, Blade templates, jQuery, "
            "MySQL, phpMyAdmin, Eloquent migrations, "
            "Git, XAMPP, Postman, Filament admin panel, MVC architecture.\n\n"
            "FINAL YEAR PROJECT\n"
            "Hotel Sewa — Hotel Booking and Management System. "
            "Laravel 10 full-stack covering room types, booking calendar, "
            "check-in/check-out, billing, and staff management with Filament. "
            "12-table MySQL schema with soft deletes. "
            "NTC payment gateway sandbox for online bookings. "
            "Laravel Queues + Mailtrap confirmation emails.\n\n"
            "MINOR PROJECT\n"
            "Online Exam System — PHP/MySQL timed MCQ platform for lecturers "
            "and students; auto-graded with result history.\n\n"
            "ACHIEVEMENTS\n"
            "Completed Laracasts Laravel From Scratch series (2024). "
            "Volunteer developer, Open Source Kathmandu (NGO portal contribution)."
        ),
    },
    {
        "email":     "nisha.shrestha@email.com",
        "password":  "pass1234",
        "full_name": "Nisha Shrestha",
        "headline":  "BE Computer Engineering Graduate · ML / Data Science",
        "location":  "Kathmandu, Nepal",
        "skills":    ["Python", "Flask", "scikit-learn", "NumPy", "Pandas",
                      "TensorFlow", "SQL", "Git", "Data Visualization"],
        "resume_text": (
            "Nisha Shrestha\n"
            "Kathmandu, Nepal | nisha.shrestha@email.com\n\n"
            "EDUCATION\n"
            "BE Computer Engineering — Tribhuvan University, Kathmandu Engineering "
            "College (KEC) Kalimati, 2025. CGPA 3.5/4.0\n\n"
            "SKILLS\n"
            "Python, scikit-learn, TensorFlow, Keras, XGBoost, Pandas, NumPy, "
            "Matplotlib, Seaborn, feature engineering, model evaluation, "
            "NLP (NLTK, TF-IDF, word2vec basics), Flask, SQLAlchemy, "
            "PostgreSQL, SQLite, SQL, Git, Jupyter, Google Colab, MLflow (basics).\n\n"
            "FINAL YEAR PROJECT\n"
            "Credit Risk Assessment Model for Nepali Microfinance Institutions. "
            "1,200 anonymised loan records; 18 engineered features. "
            "Compared Logistic Regression, Random Forest, XGBoost — "
            "XGBoost achieved F1 0.84 on held-out test set. "
            "Flask web app for loan officers with SHAP explanation plots.\n\n"
            "MINOR PROJECT\n"
            "Nepali News Article Classifier — TF-IDF + Logistic Regression across "
            "6 categories; scraped Setopati & OnlineKhabar; 82% accuracy.\n\n"
            "ACHIEVEMENTS\n"
            "Kaggle Notebooks Expert, top 10% tabular classification competition. "
            "Andrew Ng Machine Learning Specialisation (Coursera, 2024)."
        ),
    },
]

# ---------------------------------------------------------------------------
# Jobs — 10 real Kathmandu IT companies
# ---------------------------------------------------------------------------
JOBS = [
    {
        "title":       "Junior Machine Learning Engineer",
        "company":     "Fusemachines",
        "location":    "Kathmandu, Nepal (Hybrid)",
        "job_type":    "full_time",
        "salary_text": "NPR 55,000 – 85,000 / month",
        "skills":      ["Python", "scikit-learn", "TensorFlow", "NLP", "Pandas", "Git"],
        "description": (
            "Fusemachines is looking for a Junior ML Engineer to join our AI team "
            "building NLP and computer vision pipelines for international clients. "
            "Requirements: solid Python, hands-on scikit-learn or TensorFlow, "
            "NLP fundamentals (tokenisation, TF-IDF, embeddings). "
            "Fresh graduates with strong ML final-year projects are encouraged to apply. "
            "Experience with Pandas for data cleaning is essential."
        ),
    },
    {
        "title":       "Frontend Developer (React / Next.js)",
        "company":     "Leapfrog Technology",
        "location":    "Lalitpur, Nepal (On-site)",
        "job_type":    "full_time",
        "salary_text": "NPR 50,000 – 80,000 / month",
        "skills":      ["React", "TypeScript", "Next.js", "Tailwind CSS",
                        "REST APIs", "Git"],
        "description": (
            "Leapfrog Technology is hiring a Frontend Developer to translate Figma "
            "designs into accessible React components and integrate REST APIs. "
            "Required: React, TypeScript, Next.js App Router, Tailwind CSS. "
            "Strong portfolio of React projects is a major advantage. "
            "Agile team — sprint planning, code reviews."
        ),
    },
    {
        "title":       "Data Analyst Intern",
        "company":     "Khalti Digital Wallet",
        "location":    "Kathmandu, Nepal (On-site)",
        "job_type":    "internship",
        "salary_text": "NPR 18,000 – 25,000 / month",
        "skills":      ["SQL", "Python", "Pandas", "Excel",
                        "Data Visualization", "Power BI"],
        "description": (
            "Khalti, Nepal's leading digital wallet, needs a Data Analyst Intern "
            "for reporting, dashboards, and exploratory analysis of transaction data. "
            "Write SQL against our PostgreSQL data warehouse, build Power BI dashboards, "
            "and present findings to product managers. "
            "Strong SQL is non-negotiable. Python (Pandas) is a plus."
        ),
    },
    {
        "title":       "Backend Developer (Django)",
        "company":     "eSewa — F1Soft Group",
        "location":    "Kathmandu, Nepal (On-site)",
        "job_type":    "full_time",
        "salary_text": "NPR 65,000 – 100,000 / month",
        "skills":      ["Python", "Django", "PostgreSQL", "Docker",
                        "REST APIs", "Git"],
        "description": (
            "eSewa, Nepal's first digital payment service, is expanding its backend team. "
            "Build and maintain REST APIs, write Django ORM queries and migrations, "
            "and participate in system design discussions. "
            "Required: Django REST Framework, PostgreSQL, Docker. "
            "Nice to have: Redis, Celery, PCI-DSS basics."
        ),
    },
    {
        "title":       "Junior NLP / AI Engineer",
        "company":     "Docsumo",
        "location":    "Kathmandu, Nepal (Remote)",
        "job_type":    "full_time",
        "salary_text": "NPR 60,000 – 90,000 / month",
        "skills":      ["Python", "NLP", "spaCy", "TensorFlow", "scikit-learn", "Git"],
        "description": (
            "Docsumo builds AI document-understanding products used globally. "
            "Junior NLP Engineer role: fine-tune NER models, evaluate extraction accuracy, "
            "preprocess training datasets. "
            "Must have: Python, spaCy or NLTK or Transformers hands-on experience, "
            "understanding of precision/recall/F1. "
            "Final-year NLP thesis or project is a strong differentiator."
        ),
    },
    {
        "title":       "QA Automation Engineer",
        "company":     "Verisk Nepal",
        "location":    "Lalitpur, Nepal (On-site)",
        "job_type":    "full_time",
        "salary_text": "NPR 45,000 – 70,000 / month",
        "skills":      ["Python", "Selenium", "Jest", "Postman", "SQL", "Git"],
        "description": (
            "Verisk Nepal delivers data analytics for global insurance. "
            "QA Automation Engineer: own test automation for web apps, "
            "integrate tests into CI/CD pipeline. "
            "Write Selenium + pytest scripts, maintain Postman API collections, "
            "triage failures. ISTQB CTFL is a bonus."
        ),
    },
    {
        "title":       "Full-Stack Developer (MERN)",
        "company":     "Deerwalk Services",
        "location":    "Kathmandu, Nepal (Hybrid)",
        "job_type":    "full_time",
        "salary_text": "NPR 60,000 – 95,000 / month",
        "skills":      ["JavaScript", "Node.js", "React", "Express.js",
                        "MongoDB", "REST APIs", "Git"],
        "description": (
            "Deerwalk Services builds healthcare technology for the US market. "
            "Full-Stack Developer on patient-facing web portals using MERN stack. "
            "Build REST APIs in Node.js/Express, design MongoDB schemas, implement "
            "React UIs. TypeScript or CI/CD experience is a plus."
        ),
    },
    {
        "title":       "Junior Android Developer",
        "company":     "eSewa — F1Soft Group",
        "location":    "Kathmandu, Nepal (On-site)",
        "job_type":    "full_time",
        "salary_text": "NPR 55,000 – 80,000 / month",
        "skills":      ["Android", "Kotlin", "Java", "Firebase", "REST APIs", "Git"],
        "description": (
            "Join the eSewa mobile team and build features used by 7 million Nepali users. "
            "Implement Kotlin screens following MVVM, integrate REST APIs with Retrofit, "
            "write unit tests. "
            "Required: Kotlin, Android SDK, Jetpack, Firebase. "
            "Published Play Store app is a strong plus."
        ),
    },
    {
        "title":       "Junior DevOps / Systems Engineer",
        "company":     "Cotiviti Nepal",
        "location":    "Lalitpur, Nepal (On-site)",
        "job_type":    "full_time",
        "salary_text": "NPR 55,000 – 85,000 / month",
        "skills":      ["Docker", "Linux", "CI/CD", "Git", "Python", "PostgreSQL"],
        "description": (
            "Cotiviti Nepal needs a Junior DevOps Engineer to maintain Linux servers, "
            "write Docker Compose files, set up GitHub Actions workflows, and monitor "
            "services. Required: Linux CLI, Docker, Git, Bash/Python scripting. "
            "Kubernetes or AWS is a bonus."
        ),
    },
    {
        "title":       "PHP Laravel Developer",
        "company":     "Yomari Inc.",
        "location":    "Kathmandu, Nepal (On-site)",
        "job_type":    "full_time",
        "salary_text": "NPR 45,000 – 70,000 / month",
        "skills":      ["PHP", "Laravel", "MySQL", "JavaScript",
                        "Bootstrap", "REST APIs", "Git"],
        "description": (
            "Yomari is a Kathmandu web-solutions company. PHP Laravel Developer: "
            "build Eloquent models, Blade templates, REST API endpoints, MySQL migrations. "
            "Requirements: Laravel 9/10, MySQL, Blade, Bootstrap. "
            "Livewire or Filament experience is a plus."
        ),
    },
]


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seed realistic Kathmandu IT-graduate data for the matching engine."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove existing seeded users and jobs before re-seeding.",
        )

    def handle(self, *args, **options) -> None:
        if options["clear"]:
            self._clear()
        skill_map = self._seed_skills()
        self._seed_employer_and_jobs(skill_map)
        self._seed_candidates(skill_map)
        self.stdout.write(self.style.SUCCESS(
            "\nRealistic demo data seeded. Candidate logins: <email> / pass1234"
        ))

    # ------------------------------------------------------------------
    def _clear(self) -> None:
        emails = [c["email"] for c in CANDIDATES] + ["employer@skillmatch.np"]
        deleted, _ = User.objects.filter(email__in=emails).delete()
        self.stdout.write(f"Cleared {deleted} existing demo users.")

    # ------------------------------------------------------------------
    def _seed_skills(self) -> dict:
        skill_map: dict[str, Skill] = {}
        for name, category in SKILLS:
            skill, _ = Skill.objects.get_or_create(
                name=name, defaults={"category": category}
            )
            skill_map[name] = skill
        self.stdout.write(self.style.SUCCESS(f"Skills ready: {len(skill_map)}"))
        return skill_map

    # ------------------------------------------------------------------
    def _seed_employer_and_jobs(self, skill_map: dict) -> None:
        employer, created = User.objects.get_or_create(
            email="employer@skillmatch.np",
            defaults={
                "full_name": "SkillMatch Demo Employer",
                "role":      User.Role.EMPLOYER,
            },
        )
        if created:
            employer.set_password("pass1234")
            employer.save()

        for spec in JOBS:
            job, made = Job.objects.get_or_create(
                title=spec["title"],
                employer=employer,
                defaults={
                    "company":     spec["company"],
                    "location":    spec["location"],
                    "job_type":    spec["job_type"],
                    "salary_text": spec["salary_text"],
                    "description": spec["description"],
                    "is_active":   True,
                },
            )
            if made:
                job.required_skills.set(
                    skill_map[s] for s in spec["skills"] if s in skill_map
                )
        count = Job.objects.filter(employer=employer).count()
        self.stdout.write(self.style.SUCCESS(f"Jobs ready: {count}"))

    # ------------------------------------------------------------------
    def _seed_candidates(self, skill_map: dict) -> None:
        for spec in CANDIDATES:
            user, created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "full_name": spec["full_name"],
                    "role":      User.Role.CANDIDATE,
                },
            )
            if created:
                user.set_password(spec["password"])
                user.save()

            # Profile
            profile, _ = CandidateProfile.objects.get_or_create(user=user)
            profile.headline = spec["headline"]
            profile.location = spec["location"]
            candidate_skills = [
                skill_map[s] for s in spec["skills"] if s in skill_map
            ]
            profile.skills.set(candidate_skills)
            profile.resume_score = min(50 + len(candidate_skills) * 5, 100)
            profile.save(update_fields=["headline", "location", "resume_score"])

            # Resume (raw text — no file upload needed in seed)
            resume, _ = Resume.objects.get_or_create(
                candidate=user,
                defaults={
                    "original_filename": "resume.pdf",
                    "is_primary":        True,
                },
            )
            resume.raw_text  = spec["resume_text"].strip()
            resume.is_primary = True
            resume.save(update_fields=["raw_text", "is_primary"])
            resume.extracted_skills.set(candidate_skills)

            self.stdout.write(f"  Seeded: {spec['full_name']} ({spec['headline']})")

        self.stdout.write(self.style.SUCCESS(f"Candidates ready: {len(CANDIDATES)}"))
