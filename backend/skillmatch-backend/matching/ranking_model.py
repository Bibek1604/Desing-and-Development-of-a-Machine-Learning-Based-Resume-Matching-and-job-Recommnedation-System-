"""ML Candidate–Job Ranking Model.

Uses a feature-engineered gradient-boosting model (LightGBM preferred,
XGBoost fallback, scikit-learn GBM as final fallback) to produce a 0-100
match score.

Features used
-------------
  skill_overlap      float  fraction of job skills matched
  semantic_sim       float  sentence-BERT cosine similarity
  tfidf_sim          float  TF-IDF cosine similarity
  cgpa_norm          float  CGPA normalised to [0,1] (scale 0-4)
  has_degree         int    1 if degree matches job level expectation
  has_internship     int    1 if candidate has internship experience
  has_github         int    1 if GitHub link present
  cert_count         int    number of certifications (capped at 5)
  skill_count        int    total technical skills (capped at 20)
  exp_years          float  estimated work experience in years
  preferred_match    int    1 if preferred role matches job title
  text_length_norm   float  resume text length normalised

The model trains on real score labels produced by the hybrid matcher
(treat hybrid score as ground truth for the ranking learner).

Usage — inference (no training needed; uses heuristic model by default)
-----------------------------------------------------------------------
    from matching.ranking_model import CandidateJobRanker
    ranker = CandidateJobRanker()
    score = ranker.score(user, job)           # 0-100 int
    explanation = ranker.explain(user, job)   # dict with feature importances
"""
from __future__ import annotations
import re
import math
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accounts.models import User
    from jobs.models import Job

log = logging.getLogger(__name__)

# Feature vector order shared by training (train_ranker) and inference, so a
# model trained on these columns lines up exactly with score()'s feature dict.
FEATURE_ORDER = [
    "skill_overlap", "semantic_sim", "tfidf_sim", "cgpa_norm", "has_internship",
    "has_github", "cert_count", "skill_count", "exp_years", "preferred_match",
]
MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "ranker.joblib"
_MODEL = None
_MODEL_TRIED = False


def _get_model():
    """Lazily load the trained ranking model artifact, if one exists."""
    global _MODEL, _MODEL_TRIED
    if not _MODEL_TRIED:
        _MODEL_TRIED = True
        try:
            import joblib
            if MODEL_PATH.exists():
                _MODEL = joblib.load(MODEL_PATH)
                log.info("Loaded trained ranker model from %s", MODEL_PATH)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not load ranker model (%s); using heuristic weights.", exc)
            _MODEL = None
    return _MODEL


def reload_model():
    """Force the model artifact to be re-read (used right after training)."""
    global _MODEL, _MODEL_TRIED
    _MODEL = None
    _MODEL_TRIED = False
    return _get_model()


def _feat_exp_years(resume_text: str) -> float:
    """Estimate years of work experience from resume text.

    Deliberately the same loose ``(\\d+)\\s*year`` pattern the trainer uses
    (matching.training._profile_meta). The stricter
    "N years of experience/work" phrasing this used to require matched far
    fewer resumes at serve time than at train time, so the model saw a
    systematically smaller exp_years in production than it was fitted on.
    """
    hits = re.findall(r"(\d+)\s*year", resume_text or "", re.I)
    if hits:
        return min(float(max(int(h) for h in hits)), 10.0)
    return 0.0


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class CandidateJobRanker:
    """Hybrid heuristic + optional ML ranker."""

    # Feature weights learned from synthetic calibration data
    # (tune or replace with a trained model via .fit())
    _WEIGHTS = {
        "skill_overlap":     35.0,
        "semantic_sim":      25.0,
        "tfidf_sim":         10.0,
        "cgpa_norm":          5.0,
        "has_internship":     5.0,
        "has_github":         3.0,
        "cert_count":         4.0,
        "skill_count":        5.0,
        "exp_years":          5.0,
        "preferred_match":    3.0,
    }

    def _build_features(self, user, job, sim=None, cand=None) -> dict:
        """Feature dict for one (candidate, job) pair.

        ``sim``  -- precomputed corpus-level similarity for this pair. Callers
                    that already ran the fitted index (matching.services) pass
                    it in; recomputing here would re-fit a TF-IDF vectorizer on
                    a 2-document corpus, which is both slow (seconds per
                    request) and *wrong* -- the IDF statistics would not match
                    the ones the model was trained on (train/serve skew).
        ``cand`` -- precomputed (resume_text, normalized_skills) tuple, so a
                    shortlist of N jobs costs one profile query, not N.
        """
        from matching.services import (
            _candidate_text_and_skills, normalize_skill, _calibrate,
        )

        profile = getattr(user, "candidate_profile", None)
        resume_text, cand_skills = cand if cand is not None else _candidate_text_and_skills(user)
        # normalize_skill on both sides -- training normalizes too, so an
        # un-normalized set here would shift skill_overlap at serve time only.
        job_skills = {normalize_skill(s) for s in job.required_skills.values_list("name", flat=True)}

        # Plain coverage fraction -- must match training's definition exactly.
        # services._skill_overlap adds a +0.04/skill display bonus that training
        # never applied; using it here inflates the feature at inference only.
        overlap = (len(cand_skills & job_skills) / len(job_skills)) if job_skills else 0.0

        if sim is None:
            from matching.index import get_job_index
            try:
                index = get_job_index()
                pos = next(i for i, j in enumerate(index.jobs) if j.pk == job.pk)
                sim = index.similarities(resume_text)[pos]
            except Exception:
                sim = 0.0
        # One text signal feeds both slots: the shipped artifact was trained
        # with semantic_sim falling back to the TF-IDF value whenever
        # sentence-transformers was unavailable.
        tfidf_sim = float(sim)
        sem_sim = float(sim)

        cgpa = float(profile.cgpa or 0) if profile else 0.0
        cgpa_norm = min(cgpa / 4.0, 1.0)

        has_internship = 1 if resume_text and re.search(r"\bintern\b", resume_text, re.I) else 0
        has_github = 1 if (profile and profile.github_url) else (
            1 if resume_text and "github.com" in resume_text.lower() else 0
        )
        certs = profile.certifications_list() if profile else []
        cert_count = min(len(certs), 5) / 5.0

        skill_count = min(len(profile.skills_list()) if profile else len(cand_skills), 20) / 20.0
        exp_years   = _feat_exp_years(resume_text) / 10.0

        # Training matches on the FIRST WORD of preferred_role ("Backend" in
        # "Senior Backend Developer"); a whole-string test here would score 0
        # on titles training scored 1 on.
        preferred = (profile.preferred_role or "").lower() if profile else ""
        first = preferred.split()[0] if preferred.split() else ""
        preferred_match = 1 if first and first in job.title.lower() else 0

        return {
            "skill_overlap":    overlap,
            "semantic_sim":     sem_sim,
            "tfidf_sim":        tfidf_sim,
            "cgpa_norm":        cgpa_norm,
            "has_internship":   has_internship,
            "has_github":       has_github,
            "cert_count":       cert_count,
            "skill_count":      skill_count,
            "exp_years":        exp_years,
            "preferred_match":  preferred_match,
        }

    def shortlist_probability(self, user, job, sim=None, cand=None) -> float:
        """P(employer shortlists this candidate), in [0, 1], or None.

        A *classifier probability*, not a match percentage -- reported
        alongside the match score, never as it.
        """
        out = self.shortlist_probabilities(user, [(job, sim)], cand=cand)
        return out.get(job.pk)

    def shortlist_probabilities(self, user, job_sims, cand=None) -> dict:
        """Batched form: {job_id: probability} for [(job, sim), ...].

        One ``predict_proba`` call for the whole shortlist. Scoring pairs one
        at a time re-entered joblib's parallel dispatch per row, which cost
        ~85 ms of pure scheduling overhead each (2.5 s for a 30-job shortlist)
        while the arithmetic itself is microseconds.
        """
        model = _get_model()
        if model is None or not job_sims:
            return {}
        try:
            rows, ids = [], []
            for job, sim in job_sims:
                feats = self._build_features(user, job, sim=sim, cand=cand)
                rows.append([float(feats.get(k, 0.0)) for k in FEATURE_ORDER])
                ids.append(job.pk)
            probs = model.predict_proba(rows)[:, 1]
            return {jid: float(p) for jid, p in zip(ids, probs)}
        except Exception as exc:  # noqa: BLE001
            log.warning("Trained ranker failed (%s); falling back to content score.", exc)
            return {}

    def score(self, user, job, sim=None, cand=None) -> int:
        """Return the 0-100 *match* score for one (candidate, job) pair.

        Delegates to the SAME ``services._combine`` the recommendation and
        employer-ranking pipelines use, so /recommendations, /explain and
        Application.match_score can never disagree about one pair (they used
        to: model probability 53 vs heuristic 4 for the same pair).
        """
        from matching.services import (
            _candidate_text_and_skills, _combine, _skill_overlap, normalize_skill,
        )
        resume_text, cand_skills = cand if cand is not None else _candidate_text_and_skills(user)
        job_skills = {normalize_skill(s) for s in job.required_skills.values_list("name", flat=True)}
        overlap, _ = _skill_overlap(cand_skills, job_skills)
        if sim is None:
            from matching.index import get_job_index
            try:
                index = get_job_index()
                pos = next(i for i, j in enumerate(index.jobs) if j.pk == job.pk)
                sim = index.similarities(resume_text)[pos]
            except Exception:
                sim = 0.0
        return _combine(sim, overlap)

    def explain(self, user, job, sim=None, cand=None) -> dict:
        """Return feature contributions for explainable AI output.

        ``score`` here is the same number ``score()`` returns for this pair --
        this method used to report its own heuristic total instead, so the
        /explain endpoint contradicted the score shown on the job card.
        """
        feats = self._build_features(user, job, sim=sim, cand=cand)
        score = self.score(user, job, sim=sim, cand=cand)
        total = sum(self._WEIGHTS[k] * feats.get(k, 0.0) for k in self._WEIGHTS)

        contributions = []
        for feat, weight in sorted(self._WEIGHTS.items(), key=lambda x: -x[1]):
            val    = feats.get(feat, 0.0)
            pts    = weight * val
            pct    = round(pts / total * 100, 1) if total > 0 else 0.0
            contributions.append({
                "feature":      feat,
                "value":        round(val, 3),
                "contribution": round(pts, 1),
                "pct_of_score": pct,
            })

        profile = getattr(user, "candidate_profile", None)
        job_skills = list(job.required_skills.values_list("name", flat=True))
        from matching.services import _candidate_text_and_skills
        _, cand_skills = _candidate_text_and_skills(user)
        job_skills_lower = {s.lower() for s in job_skills}
        matched  = [s for s in job_skills if s.lower() in cand_skills]
        missing  = [s for s in job_skills if s.lower() not in cand_skills]

        reasons = _build_reasons(feats, matched, missing)

        return {
            "score":              score,
            "feature_contributions": contributions,
            "matched_skills":     matched,
            "missing_skills":     missing[:5],
            "reasons":            reasons,
            "explanation_summary": _summarise(score, feats, matched, missing),
        }


def _build_reasons(feats: dict, matched: list, missing: list) -> list[str]:
    reasons = []
    if feats["skill_overlap"] >= 0.8:
        reasons.append(f"Excellent skill match — {int(feats['skill_overlap']*100)}% of required skills present")
    elif feats["skill_overlap"] >= 0.5:
        reasons.append(f"Good skill match — {int(feats['skill_overlap']*100)}% of required skills")
    else:
        reasons.append(f"Low skill overlap — only {int(feats['skill_overlap']*100)}% of required skills")

    if feats["semantic_sim"] >= 0.7:
        reasons.append("Resume text is semantically very similar to the job description")
    elif feats["semantic_sim"] >= 0.4:
        reasons.append("Moderate semantic similarity to job description")

    if feats["has_internship"]:
        reasons.append("Internship experience detected — relevant to this role")
    if feats["has_github"]:
        reasons.append("GitHub profile present — demonstrates practical work")
    if feats["cgpa_norm"] >= 0.875:  # 3.5+
        reasons.append("High academic performance (3.5+ CGPA)")
    if feats["cert_count"] > 0:
        reasons.append("Certifications present — adds credibility")
    if missing:
        reasons.append(f"Top missing skills: {', '.join(missing[:3])}")
    return reasons


def _summarise(score: int, feats: dict, matched: list, missing: list) -> str:
    level = "Strong" if score >= 75 else ("Moderate" if score >= 50 else "Weak")
    return (
        f"{level} match (score {score}/100). "
        f"Skill overlap: {int(feats['skill_overlap']*100)}%. "
        f"Matched: {', '.join(matched[:3]) or 'none'}. "
        f"Key gaps: {', '.join(missing[:3]) or 'none'}."
    )
