"""Process-local prebuilt TF-IDF indexes over jobs and candidates.

Replaces the previous per-request "fit on [query] + all documents" approach:
the vectorizer is fitted once over the corpus and only the query is
transformed per request, which is both faster (ms instead of seconds) and
more correct IR-wise (stable IDF statistics).

The cache is versioned by cheap DB aggregates and rebuilt automatically when
the underlying data changes. Plain in-process memory — no Redis needed.
"""
from __future__ import annotations

import logging
import threading

from django.db.models import Count, Max

logger = logging.getLogger("skillmatch.matching")

_lock = threading.Lock()
_job_cache: tuple[tuple, "JobIndex"] | None = None
_cand_cache: tuple[tuple, "CandidateIndex"] | None = None


class _TfidfIndex:
    def __init__(self, docs: list[str]):
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401
        from .engine.tfidf import build_vectorizer

        self.vectorizer = build_vectorizer()
        self.matrix = self.vectorizer.fit_transform([d or "" for d in docs])

    def similarities(self, text: str) -> list[float]:
        from sklearn.metrics.pairwise import cosine_similarity

        q = self.vectorizer.transform([text or ""])
        return [float(s) for s in cosine_similarity(q, self.matrix).flatten()]


class JobIndex(_TfidfIndex):
    """Fitted index over all active jobs + precomputed normalized skill sets."""

    def __init__(self, jobs):
        from .services import normalize_skill

        self.jobs = jobs
        self.job_skills = [
            {normalize_skill(s) for s in j.required_skills.values_list("name", flat=True)}
            for j in jobs
        ]
        super().__init__([j.as_match_text() for j in jobs])


class CandidateIndex(_TfidfIndex):
    """Fitted index over all candidate documents."""

    def __init__(self, users, docs, skill_sets):
        self.users = users
        self.skill_sets = skill_sets
        super().__init__(docs)


def _job_version():
    from jobs.models import Job

    agg = Job.objects.filter(is_active=True).aggregate(
        n=Count("id"), mx=Max("id"), latest=Max("posted_at")
    )
    return (agg["n"], agg["mx"], str(agg["latest"]))


def _candidate_version():
    from accounts.models import CandidateProfile
    from resumes.models import Resume

    agg = CandidateProfile.objects.aggregate(n=Count("id"), latest=Max("updated_at"))
    r = Resume.objects.aggregate(latest=Max("uploaded_at"))
    return (agg["n"], str(agg["latest"]), str(r["latest"]))


def get_job_index() -> JobIndex:
    global _job_cache
    version = _job_version()
    with _lock:
        if _job_cache and _job_cache[0] == version:
            return _job_cache[1]
    from jobs.models import Job

    jobs = list(Job.objects.filter(is_active=True).prefetch_related("required_skills"))
    index = JobIndex(jobs)
    with _lock:
        _job_cache = (version, index)
    logger.info("Job index rebuilt: %d jobs", len(jobs))
    return index


def get_candidate_index() -> CandidateIndex:
    global _cand_cache
    version = _candidate_version()
    with _lock:
        if _cand_cache and _cand_cache[0] == version:
            return _cand_cache[1]
    from accounts.models import CandidateProfile
    from .services import candidate_text_and_skills

    profiles = list(
        CandidateProfile.objects.select_related("user")
        .prefetch_related("user__resumes", "skills")
    )
    users, docs, skill_sets = [], [], []
    for p in profiles:
        text, skills = candidate_text_and_skills(p.user)
        users.append(p.user)
        docs.append(text)
        skill_sets.append(skills)
    index = CandidateIndex(users, docs, skill_sets)
    with _lock:
        _cand_cache = (version, index)
    logger.info("Candidate index rebuilt: %d candidates", len(users))
    return index
