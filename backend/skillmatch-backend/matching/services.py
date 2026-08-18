"""Matching services: turn resumes + jobs into ranked, scored recommendations.

Pipeline (v3 -- ranker + collab boost):
  1. Candidate document = resume text + profile summary + preferred role +
     normalized skills (richer signal than resume-only).
  2. Semantic similarity from a prebuilt TF-IDF index (1-2 grams,
     sublinear tf), calibrated with a square-root transform.
  3. Skill overlap computed on *normalized* skill names (synonyms like
     "reactjs" -> "react", suffix strip like "Python Fundamentals" -> "python").
  4. Hybrid content score = w1 * sqrt(similarity) + w2 * overlap, 0-100.
  5. Trained RandomForest ranker (if the artifact is present) re-ranks the
     hybrid top-N so every scoring surface -- recommendations, employer
     ranking, and Application.match_score -- uses one score model.
  6. Item-item collaborative signal (users who applied to X also applied
     to Y) is blended into the final score so co-application patterns can
     surface jobs that content similarity misses.
"""
import math

from django.conf import settings

from jobs.models import Job
from .engine import get_matcher

# --- Skill normalization ----------------------------------------------------

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


def normalize_skill(name):
    """Canonical lowercase form of a skill name for overlap comparison."""
    n = (name or "").strip().lower()
    for suffix in _SKILL_SUFFIXES:
        if n.endswith(suffix):
            n = n[: -len(suffix)]
            break
    return _SKILL_SYNONYMS.get(n, n)


# --- Scoring helpers --------------------------------------------------------

def _weights():
    w = getattr(settings, "MATCH_WEIGHTS", {"similarity": 0.6, "skill_overlap": 0.4})
    return w.get("similarity", 0.6), w.get("skill_overlap", 0.4)


def _calibrate(similarity):
    """Spread raw short-text cosine values over a usable [0, 1] range."""
    return math.sqrt(max(0.0, min(1.0, similarity)))


def _skill_overlap(candidate_skills, job_skills):
    """Coverage of the job's requirements with a small absolute bonus."""
    if not job_skills:
        return 0.0, []
    matched = candidate_skills & job_skills
    coverage = len(matched) / len(job_skills)
    bonus = 0.04 * min(len(matched), 4)
    return min(1.0, coverage + bonus), sorted(matched)


def _combine(similarity, overlap):
    w_sim, w_overlap = _weights()
    score = (w_sim * _calibrate(similarity) + w_overlap * overlap) * 100
    return max(0, min(100, int(round(score))))


def candidate_text_and_skills(user):
    """Candidate document + normalized skill set."""
    resumes = list(user.resumes.all())
    resume = next((r for r in resumes if r.is_primary), resumes[0] if resumes else None)
    parts = []
    if resume and resume.raw_text:
        parts.append(resume.raw_text)

    profile = getattr(user, "candidate_profile", None)
    skills = set()
    if profile is not None:
        skills = {normalize_skill(s) for s in profile.skills.values_list("name", flat=True)}
        for field in ("resume_summary", "career_objective", "preferred_role", "degree"):
            value = getattr(profile, field, "") or ""
            if value:
                parts.append(str(value))
        if profile.preferred_role:
            parts.append(profile.preferred_role)
    if skills:
        parts.append(" ".join(sorted(skills)))

    return " ".join(parts), skills


# Backwards-compatible alias (older imports use the underscore name).
_candidate_text_and_skills = candidate_text_and_skills


def _use_index():
    backend = getattr(settings, "MATCHER_BACKEND", "tfidf").lower()
    return backend == "tfidf"


# --- Trained-ranker + collab helpers ---------------------------------------

def _rerank_with_trained_model(user, shortlist, cand):
    """Shortlist probability per job: {job_id: float in [0, 1]}.

    Used for ORDERING only -- the number displayed to the user stays the
    interpretable hybrid content score. Returns {} if the artifact is absent
    or the ranker fails, in which case ordering falls back to that same score.

    ``cand`` and each row's precomputed ``sim`` are threaded through so the
    ranker reuses the fitted corpus index instead of re-fitting a TF-IDF
    vectorizer per (candidate, job) pair -- that refit made a single
    recommendation request take 3-11 seconds and produced IDF statistics the
    model was never trained on.
    """
    try:
        from .ranking_model import CandidateJobRanker, _get_model
        if _get_model() is None:
            return {}
        return CandidateJobRanker().shortlist_probabilities(
            user, [(r["job"], r["raw_sim"]) for r in shortlist], cand=cand,
        )
    except Exception:
        return {}


def _collab_boost_for_candidate(user, candidate_job_ids):
    """Item-item collaborative-filtering boost keyed by job id, values in [0, 1].

    boost(J) = (# peers who applied to both J and any job C already applied to)
                / max_peer_count

    Peers = other users who applied to any of C's jobs. If C has no
    applications, everyone gets 0 -- recs degrade to content-only.
    """
    try:
        from applications.models import Application
        from collections import Counter
    except Exception:
        return {}

    applied = list(
        Application.objects
        .filter(candidate=user)
        .values_list("job_id", flat=True)
    )
    if not applied:
        return {}

    peer_ids = list(
        Application.objects
        .filter(job_id__in=applied)
        .exclude(candidate=user)
        .values_list("candidate_id", flat=True)
        .distinct()[:5000]
    )
    if not peer_ids:
        return {}

    counts = Counter(
        Application.objects
        .filter(candidate_id__in=peer_ids, job_id__in=candidate_job_ids)
        .exclude(job_id__in=applied)
        .values_list("job_id", flat=True)
    )
    if not counts:
        return {}
    top = max(counts.values())
    return {jid: c / top for jid, c in counts.items()}


# --- Public API -------------------------------------------------------------

def recommend_jobs_for_candidate(user, limit=20):
    """Return [{job, score, similarity, matched_skills}] ranked best-first.

    Two-stage pipeline:
      1. Hybrid content matcher shortlists top ~2xlimit jobs (fast, index-backed).
      2. Trained RandomForest ranker (if the artifact is present) re-ranks
         the shortlist and provides the final score. Otherwise the hybrid
         score is used.
      3. Collaborative-filtering boost (item-item co-application) is blended
         into the final score -- users who applied to X also applied to Y.
    """
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

    # Stage 1: hybrid shortlist
    shortlist = []
    for job, sim, job_skills in zip(jobs, sims, job_skill_sets):
        overlap, matched = _skill_overlap(cand_skills, job_skills)
        display = {normalize_skill(s.name): s.name for s in job.required_skills.all()}
        shortlist.append({
            "job":            job,
            "raw_sim":        float(sim),
            "hybrid_score":   _combine(sim, overlap),
            "similarity":     int(round(_calibrate(sim) * 100)),
            "matched_skills": [display.get(m, m) for m in matched],
        })
    shortlist.sort(key=lambda r: r["hybrid_score"], reverse=True)
    shortlist = shortlist[: max(30, limit * 2)]
    if not shortlist:
        return []

    # Stage 2: trained-ranker probabilities (ordering signal only)
    probs = _rerank_with_trained_model(user, shortlist, (resume_text, cand_skills))

    # Stage 3: collaborative-filtering boost
    collab = _collab_boost_for_candidate(user, [r["job"].pk for r in shortlist])

    results = []
    for r in shortlist:
        # ``score`` is the interpretable content match (weighted skill coverage
        # + calibrated text similarity) and the list is sorted by it, so the
        # ranking a user sees is always monotonic in the number shown.
        #
        # The trained classifier's output is reported separately as
        # ``shortlist_probability`` rather than driving the order: measured on
        # this dataset it reaches AUC 0.58 and a cross-validated accuracy equal
        # to the majority-class baseline, so there is no evidence it orders
        # candidates better than the content score. Promote it to the sort key
        # once it beats the baseline on held-out data.
        boost = collab.get(r["job"].pk, 0)
        results.append({
            "job":            r["job"],
            "score":          max(0, min(100, int(round(r["hybrid_score"] * 0.85 + boost * 15)))),
            "similarity":     r["similarity"],
            "matched_skills": r["matched_skills"],
            "shortlist_probability": round(probs[r["job"].pk], 4) if r["job"].pk in probs else None,
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def rank_candidates_for_job(job, limit=20):
    """Return [{candidate, score, similarity, matched_skills}] ranked best-first.

    Same two-stage design as candidate-side: hybrid shortlist, then trained
    ranker rerank so employers see the same score model as candidates.
    """
    job_text = job.as_match_text()
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

    shortlist = []
    for user, sim, cand_skills in zip(users, sims, skill_sets):
        overlap, matched = _skill_overlap(cand_skills, job_skills)
        shortlist.append({
            "candidate":      user,
            "raw_sim":        float(sim),
            "cand_skills":    cand_skills,
            "hybrid_score":   _combine(sim, overlap),
            "similarity":     int(round(_calibrate(sim) * 100)),
            "matched_skills": [job_skill_display.get(m, m) for m in matched],
        })
    shortlist.sort(key=lambda r: r["hybrid_score"], reverse=True)
    shortlist = shortlist[: max(30, limit * 2)]

    try:
        from .ranking_model import CandidateJobRanker, _get_model
        ranker = CandidateJobRanker() if _get_model() is not None else None
    except Exception:
        ranker = None

    # Same contract as the candidate side: sort by the score that is displayed,
    # report the classifier probability alongside it.
    probs = {}
    if ranker is not None:
        for r in shortlist:
            p = ranker.shortlist_probability(r["candidate"], job, sim=r["raw_sim"])
            if p is not None:
                probs[r["candidate"].pk] = p

    results = [{
        "candidate":      r["candidate"],
        "score":          r["hybrid_score"],
        "similarity":     r["similarity"],
        "matched_skills": r["matched_skills"],
        "shortlist_probability": round(probs[r["candidate"].pk], 4) if r["candidate"].pk in probs else None,
    } for r in shortlist]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def score_candidate_for_job(user, job):
    """Single match score (0-100) for one candidate against one job.

    One definition of "match score" for every surface: recommendations,
    employer ranking, and the number stamped on an Application all reduce to
    ``_combine(similarity, skill_overlap)``.
    """
    resume_text, cand_skills = candidate_text_and_skills(user)
    matcher = get_matcher()
    sims = matcher.similarity(resume_text, [job.as_match_text()])
    sim = sims[0] if sims else 0.0
    job_skills = {normalize_skill(s) for s in job.required_skills.values_list("name", flat=True)}
    overlap, _ = _skill_overlap(cand_skills, job_skills)
    return _combine(sim, overlap)
