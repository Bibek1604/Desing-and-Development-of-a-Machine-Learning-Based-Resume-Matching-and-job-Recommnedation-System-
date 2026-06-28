"""Skill Gap Analyzer — compares a candidate's profile to a job's requirements.

Returns:
  missing_skills        — skills in job requirements not found in candidate
  missing_technologies  — inferred tech stack gaps (language / framework)
  missing_certifications— certs mentioned in job but missing from profile
  experience_gaps       — seniority / years-of-exp signals the candidate lacks
  matched_skills        — skills the candidate already has for this job
  match_improvement_pct — estimated score gain if all gaps are filled

Usage
-----
    from matching.skill_gap import SkillGapAnalyzer
    report = SkillGapAnalyzer().analyze(user, job)
"""
from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accounts.models import User
    from jobs.models import Job

# ── Technology cluster definitions ───────────────────────────────────────────
_TECH_CLUSTERS = {
    "containerization":  ["Docker","Kubernetes","Helm","Docker Compose"],
    "cloud":             ["AWS","Azure","GCP","Heroku","DigitalOcean"],
    "ci_cd":             ["GitHub Actions","Jenkins","GitLab CI","CircleCI","Travis CI"],
    "databases_sql":     ["PostgreSQL","MySQL","SQLite","MS SQL","Oracle"],
    "databases_nosql":   ["MongoDB","Redis","Cassandra","DynamoDB","Firebase"],
    "ml_frameworks":     ["TensorFlow","PyTorch","scikit-learn","Keras","XGBoost"],
    "frontend_modern":   ["React","Next.js","Vue.js","Angular","Svelte"],
    "backend_python":    ["Django","FastAPI","Flask"],
    "backend_js":        ["Node.js","Express.js","NestJS"],
    "mobile":            ["React Native","Flutter","Android SDK","iOS Development"],
    "testing":           ["Selenium","PyTest","Jest","Cypress","JUnit"],
}

_CERT_PATTERNS = re.compile(
    r"\b(aws|azure|gcp|google|certified|certification|certificate|comptia|cisco|"
    r"oracle|scrum|pmp|istqb|coursera|udemy|hackerrank)\b", re.I
)

_SENIOR_PATTERNS = re.compile(
    r"\b(senior|sr\.|lead|principal|architect|manager|head of|years? of experience|"
    r"3\+|4\+|5\+|6\+|7\+)\b", re.I
)


class SkillGapAnalyzer:

    def analyze(self, user, job) -> dict:
        """Full skill gap report for user ↔ job pair."""
        # ── Gather candidate data ────────────────────────────────────────
        profile = getattr(user, "candidate_profile", None)
        cand_skills_raw: list[str] = []
        cand_certs: list[str] = []
        if profile:
            cand_skills_raw = profile.skills_list()
            cand_certs = profile.certifications_list()
        cand_skills_lower = {s.lower() for s in cand_skills_raw}
        cand_certs_lower  = {c.lower() for c in cand_certs}

        # Resume text for heuristic checks
        resume = user.resumes.filter(is_primary=True).first() or user.resumes.first()
        resume_text = (resume.raw_text if resume else "").lower()

        # ── Gather job data ───────────────────────────────────────────────
        job_skills_raw: list[str] = list(job.required_skills.values_list("name", flat=True))
        job_skills_lower = {s.lower() for s in job_skills_raw}
        job_text = (job.description or "").lower()

        # ── 1. Missing skills ─────────────────────────────────────────────
        matched  = [s for s in job_skills_raw if s.lower() in cand_skills_lower]
        missing  = [s for s in job_skills_raw if s.lower() not in cand_skills_lower]

        # ── 2. Missing technology clusters ────────────────────────────────
        missing_tech: list[str] = []
        for cluster_name, cluster_skills in _TECH_CLUSTERS.items():
            # job mentions this cluster but candidate has none of it
            job_needs  = any(s.lower() in job_text for s in cluster_skills)
            cand_has   = any(s.lower() in cand_skills_lower for s in cluster_skills)
            if job_needs and not cand_has:
                # report the specific skills from this cluster that job mentions
                needed = [s for s in cluster_skills if s.lower() in job_text]
                if needed:
                    missing_tech.extend(needed)

        # ── 3. Missing certifications ─────────────────────────────────────
        missing_certs: list[str] = []
        cert_hits = _CERT_PATTERNS.findall(job_text)
        for hit in set(cert_hits):
            if hit not in cand_certs_lower and hit not in resume_text:
                missing_certs.append(hit.title())

        # ── 4. Experience gaps ────────────────────────────────────────────
        exp_gaps: list[str] = []
        if _SENIOR_PATTERNS.search(job.description or ""):
            exp_gaps.append("Role appears to require senior-level or multi-year experience")

        cgpa = float(profile.cgpa or 0) if profile else 0
        if cgpa and cgpa < 2.5:
            exp_gaps.append("CGPA below 2.5 may be screened by this employer")

        if not resume_text or len(resume_text) < 300:
            exp_gaps.append("Resume text is sparse — upload a full CV for better matching")

        # ── 5. Improvement estimate ───────────────────────────────────────
        if job_skills_raw:
            current_overlap = len(matched) / len(job_skills_raw)
            potential_overlap = 1.0  # if all gaps filled
            improvement = round((potential_overlap - current_overlap) * 100, 1)
        else:
            improvement = 0.0

        return {
            "matched_skills":         matched,
            "missing_skills":         missing,
            "missing_technologies":   list(set(missing_tech))[:10],
            "missing_certifications": list(set(missing_certs))[:5],
            "experience_gaps":        exp_gaps,
            "match_improvement_pct":  improvement,
        }
