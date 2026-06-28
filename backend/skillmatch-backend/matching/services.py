"""Matching services: turn resumes + jobs into ranked, scored recommendations.

Pipeline (v2 — accuracy pass):
  1. Candidate document = resume text + profile summary + preferred role +
     normalized skills (richer signal than resume-only).
  2. Semantic similarity from a prebuilt TF-IDF index (1-2 grams,
     sublinear tf), calibrated with a square-root transform because raw
     cosine values for short texts cluster in [0.05, 0.35].
  3. Skill overlap computed on *normalized* skill names (synonyms like
     "reactjs" -> "react", variant suffixes like "Python Fundamentals"
     -> "python") with coverage + small absolute-match bonus.
  4. Final score = w1 * calibrated_similarity + w2 * overlap, 0-100.

Non-TF-IDF backends (semantic / hybrid) still work through the generic
matcher interface and benefit from steps 1, 3 and 4.
"""
import math

from django.conf import settings

from jobs.models import Job
from .engine import get_matcher

# ── Skill normalization ───────────────────────────────────────────────────────

_SKILL_SUFFIXES = (" fundamentals", " advanced", " certification", " basics")

_SKILL_SYNONYMS = {
    "js": "javascript", "es6": "javascript",
    "ts": "typescript",
    "reactjs": "react", "react.js": "react",
    "vuejs": "vue", "vue.js": "vue",
    "nodejs": "node.js", "node": "node.js",
    "nextjs": "next.js",
    "py": "python", "python3": "python",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "k8s": "kubernetes",
    "golang": "go",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "machine learning",
    "gcloud": "gcp", "google cloud": "gcp",
    "amazon web services": "aws",
    "ci/cd": "ci-cd", "cicd": "ci-cd",
    "html5": "html", "css3": "css",
    "tailwindcss": "tailwind",
    "restful api": "rest api", "rest": "rest api",
}


def normalize_skill(name: str) -> str:
    """Canonical lowercase form of a skill name for overlap comparison."""
    n = (name or "").strip().lower()
    for suffix in _SKILL_SUFFIXES:
        if n.endswith(suffix):
            n = n[: -len(suffix)]
            break
    return _SKILL_SYNONYMS.get(n, n)


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _weights():
    w = getattr(settings, "MATCH_WEIGHTS", {"similarity": 0.6, "skill_overlap": 0.4})
    return w.get("similarity", 0.6), w.get("skill_overlap", 0.4)


def _calibrate(similarity: float) -> float:
    """Spread raw short-text cosine values over a usable [0, 1] range.

    sqrt is monotonic (ranking is preserved) but lifts the typical
    0.05-0.35 raw band to 0.22-0.59, so combined scores are meaningful.
    """
    return math.sqrt(max(0.0, min(1.0, similarity)))


def _skill_overlap(candidate_skills: set[str], job_skills: set[str]):
    """Coverage of the job's requirements with a small absolute bonus."""
    if not job_skills:
        return 0.0, []
    matched = candidate_skills & job_skills
    coverage = len(matched) / len(job_skills)
    bonus = 0.04 * min(len(matched), 4)  # rewards breadth on skill-heavy jobs
    return min(1.0, coverage + bonus), sorted(matched)


def _combine(similarity: float, overlap: float) -> int:
    w_sim, w_overlap = _weights()
    score = (w_sim * _calibrate(similarity) + w_overlap * overlap) * 100
    return max(0, min(100, int(round(score))))


def candidate_text_and_skills(user):
    """Candidate document + normalized skill set.

    Combines resume text with structured profile fields so profile-only
    users (no resume yet) still produce a meaningful document.
    """
    # Iterate the (possibly prefetched) resume set in Python — calling
    # .filter() here would bypass prefetch_related and cause N+1 queries
    # when building the candidate index over thousands of profiles.
    resumes = list(user.resumes.all())
    resume = next((r for r in resumes if r.is_primary), resumes[0] if resumes else None)
    parts = []
    if resume and resume.raw_text:
        parts.append(resume.raw_text)

    profile = getattr(user, "candidate_profile", None)
    skills: set[str] = set()
    if profile is not None:
        skills = {normalize_skill(s) for s in profile.skills.values_list("name", flat=True)}
        for field in ("resume_summary", "career_objective", "preferred_role", "degree"):
            value = getattr(profile, field, "") or ""
            if value:
                parts.append(str(value))
        # Repeat the preferred role: it is the strongest intent signal we have.
        if profile.preferred_role:
            parts.append(profile.preferred_role)
    if skills:
        parts.append(" ".join(sorted(skills)))

    return " ".join(parts), skills


# Backwards-compatible alias (older imports use the underscore name).
_candidate_text_and_skills = candidate_text_and_skills


def _use_index() -> bool:
    backend = getattr(settings, "MATCHER_BACKEND", "tfidf").lower()
    return backend == "tfidf"


# ── Public API (signatures unchanged) ─────────────────────────────────────────

def recommend_jobs_for_candidate(user, limit: int = 20):
    """Return [{job, score, similarity, matched_skills}] ranked best-first."""
    resume_text, cand_skills = candidate_text_and_skills(user)

    if _use_index():
        from .index import get_job_index

        index = get_job_index()
        if not index.jobs:
            return []
        sims = index.similarities(resume_text)
        jobs, job_skill_sets = index.jobs, index.job_skills
    else:
        jobs = list(Job.objects.filter(is_active=True).prefetch_related("required_skills"))
        if not jobs:
            return []
        matcher = get_matcher()
        sims = matcher.similarity(resume_text, [j.as_match_text() for j in jobs])
        job_skill_sets = [
            {normalize_skill(s) for s in j.required_skills.values_list("name", flat=True)}
            for j in jobs
        ]

    results = []
    for job, sim, job_skills in zip(jobs, sims, job_skill_sets):
        overlap, matched = _skill_overlap(cand_skills, job_skills)
        # Return the job's original skill labels (e.g. "REST APIs"), not the
        # lowercased normalized forms used for matching. Uses the prefetched
        # related set, so no extra query.
        display = {normalize_skill(s.name): s.name for s in job.required_skills.all()}
        results.append({
            "job": job,
            "score": _combine(sim, overlap),
            "similarity": int(round(_calibrate(sim) * 100)),
            "matched_skills": [display.get(m, m) for m in matched],
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def rank_candidates_for_job(job, limit: int = 20):
    """Return [{candidate, score, similarity, matched_skills}] ranked best-first."""
    job_text = job.as_match_text()
    # Original-cased labels keyed by their normalized form, so matched skills
    # are returned as "REST APIs" rather than the lowercased "rest apis".
    job_skill_display = {normalize_skill(s.name): s.name for s in job.required_skills.all()}
    job_skills = set(job_skill_display)

    if _use_index():
        from .index import get_candidate_index

        index = get_candidate_index()
        if not index.users:
            return []
        sims = index.similarities(job_text)
        users, skill_sets = index.users, index.skill_sets
    else:
        from accounts.models import CandidateProfile

        profiles = list(
            CandidateProfile.objects.select_related("user").prefetch_related("user__resumes", "skills")
        )
        if not profiles:
            return []
        users, docs, skill_sets = [], [], []
        for profile in profiles:
            text, skills = candidate_text_and_skills(profile.user)
            users.append(profile.user)
            docs.append(text)
            skill_sets.append(skills)
        matcher = get_matcher()
        sims = matcher.similarity(job_text, docs)

    results = []
    for user, sim, cand_skills in zip(users, sims, skill_sets):
        overlap, matched = _skill_overlap(cand_skills, job_skills)
        results.append({
            "candidate": user,
            "score": _combine(sim, overlap),
            "similarity": int(round(_calibrate(sim) * 100)),
            "matched_skills": [job_skill_display.get(m, m) for m in matched],
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def score_candidate_for_job(user, job) -> int:
    """Single match score (0-100) for one candidate against one job."""
    resume_text, cand_skills = candidate_text_and_skills(user)
    matcher = get_matcher()
    sims = matcher.similarity(resume_text, [job.as_match_text()])
    sim = sims[0] if sims else 0.0
    job_skills = {normalize_skill(s) for s in job.required_skills.values_list("name", flat=True)}
    overlap, _ = _skill_overlap(cand_skills, job_skills)
    return _combine(sim, overlap)
