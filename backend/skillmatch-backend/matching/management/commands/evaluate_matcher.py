"""
Evaluate matcher ranking quality against synthetic ground truth.

Ground truth: a job is "relevant" to a candidate when its title contains the
candidate's ``preferred_role`` (e.g. preferred_role="Backend Developer"
matches "Senior Backend Developer"). This proxy is label-independent of the
ranker's features, so the numbers are honest.

Reported metrics
----------------
    Precision@k, Recall@k, F1@k    Binary-relevance IR metrics on top-k.
    Hit@k                          Fraction of users with >=1 relevant hit in top-k.
    MRR                            Mean reciprocal rank of the first relevant hit.
    MAP@k                          Mean Average Precision at k.
    NDCG@k                         Normalised Discounted Cumulative Gain at k.
    avg latency (ms/candidate)     End-to-end recommendation time.

The command can persist the report to the currently-active
``ModelVersion.feature_importances`` under key ``"evaluation"`` so the admin
UI can display evaluation metrics next to each trained artifact.

Usage
-----
    python manage.py evaluate_matcher --sample 150 --backend tfidf --k 5
    python manage.py evaluate_matcher --sample 500 --k 10 --json report.json --persist
"""
from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

from django.core.management.base import BaseCommand


def _precision_at_k(rel, k):
    if k <= 0:
        return 0.0
    return sum(rel[:k]) / k


def _recall_at_k(rel, total_relevant, k):
    if total_relevant <= 0:
        return 0.0
    return sum(rel[:k]) / total_relevant


def _average_precision_at_k(rel, k):
    """Standard AP@k for binary relevance."""
    if not rel or k <= 0:
        return 0.0
    hits = 0
    ap = 0.0
    for i, r in enumerate(rel[:k], start=1):
        if r:
            hits += 1
            ap += hits / i
    denom = min(sum(rel), k)
    return ap / denom if denom > 0 else 0.0


def _ndcg_at_k(rel, k):
    """NDCG@k with log2 rank discount, binary gains."""
    if not rel or k <= 0:
        return 0.0
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rel[:k]))
    ideal = sorted(rel, reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


class Command(BaseCommand):
    help = "Compute Precision/Recall/F1@k, Hit@k, MRR, MAP@k, NDCG@k for the matcher."

    def add_arguments(self, parser):
        parser.add_argument("--sample",  type=int, default=150)
        parser.add_argument("--backend", type=str, default=None)
        parser.add_argument("--k",       type=int, default=5)
        parser.add_argument("--seed",    type=int, default=7)
        parser.add_argument("--json",    type=str, default=None,
                            help="Also write the full report as JSON to this path.")
        parser.add_argument("--persist", action="store_true",
                            help="Also persist the report onto the active ModelVersion row.")

    def handle(self, *args, **opts):
        from accounts.models import CandidateProfile
        from matching.services import recommend_jobs_for_candidate
        from jobs.models import Job

        rng = random.Random(opts["seed"])
        k = opts["k"]
        if opts["backend"]:
            from django.conf import settings
            settings.MATCHER_BACKEND = opts["backend"]

        profiles = list(
            CandidateProfile.objects.exclude(preferred_role="")
            .select_related("user")[:20000]
        )
        sample = rng.sample(profiles, min(opts["sample"], len(profiles)))

        # Fetch active job titles once so total-relevant per user (for Recall)
        # doesn't cost another DB round-trip per candidate.
        job_pool_titles = list(
            Job.objects.filter(is_active=True).values_list("title", flat=True)
        )

        prec_scores, rec_scores, f1_scores = [], [], []
        ap_scores, ndcg_scores, rr_scores = [], [], []
        hits = 0
        evaluated = 0

        t0 = time.time()
        for profile in sample:
            role = profile.preferred_role.lower()
            recs = recommend_jobs_for_candidate(profile.user, limit=max(k, 10))
            if not recs:
                continue
            evaluated += 1
            top = recs[:k]
            rel = [1 if role in r["job"].title.lower() else 0 for r in top]
            total_relevant = sum(1 for t in job_pool_titles if role in t.lower())

            p = _precision_at_k(rel, k)
            r = _recall_at_k(rel, total_relevant, k)
            f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

            prec_scores.append(p)
            rec_scores.append(r)
            f1_scores.append(f1)
            ap_scores.append(_average_precision_at_k(rel, k))
            ndcg_scores.append(_ndcg_at_k(rel, k))

            first = next((i for i, x in enumerate(rel) if x), None)
            rr_scores.append(1.0 / (first + 1) if first is not None else 0.0)
            if any(rel):
                hits += 1
        elapsed = time.time() - t0

        if not evaluated:
            self.stdout.write(self.style.ERROR("No candidates evaluated."))
            return

        report = {
            "backend": opts["backend"] or "settings default",
            "n": evaluated,
            "k": k,
            f"precision@{k}": round(sum(prec_scores) / len(prec_scores), 4),
            f"recall@{k}":    round(sum(rec_scores)  / len(rec_scores),  4),
            f"f1@{k}":        round(sum(f1_scores)   / len(f1_scores),   4),
            f"hit@{k}":       round(hits / evaluated, 4),
            "mrr":            round(sum(rr_scores)   / len(rr_scores),   4),
            f"map@{k}":       round(sum(ap_scores)   / len(ap_scores),   4),
            f"ndcg@{k}":      round(sum(ndcg_scores) / len(ndcg_scores), 4),
            "avg_latency_ms": round(elapsed / evaluated * 1000, 1),
        }

        self.stdout.write(self.style.SUCCESS(
            f"backend={report['backend']}  n={report['n']}\n"
            f"Precision@{k}:  {report[f'precision@{k}']:.3f}\n"
            f"Recall@{k}:     {report[f'recall@{k}']:.3f}\n"
            f"F1@{k}:         {report[f'f1@{k}']:.3f}\n"
            f"Hit@{k}:        {report[f'hit@{k}']:.3f}\n"
            f"MRR:            {report['mrr']:.3f}\n"
            f"MAP@{k}:        {report[f'map@{k}']:.3f}\n"
            f"NDCG@{k}:       {report[f'ndcg@{k}']:.3f}\n"
            f"avg latency:    {report['avg_latency_ms']:.0f} ms/candidate"
        ))

        if opts.get("json"):
            Path(opts["json"]).write_text(json.dumps(report, indent=2))
            self.stdout.write(f"Wrote JSON report to {opts['json']}")

        if opts.get("persist"):
            try:
                from matching.models import ModelVersion
                mv = ModelVersion.objects.filter(is_active=True).order_by("-version").first()
                if mv is not None:
                    fi = dict(mv.feature_importances or {})
                    fi["evaluation"] = report
                    mv.feature_importances = fi
                    mv.save(update_fields=["feature_importances"])
                    self.stdout.write(f"Persisted evaluation onto ModelVersion v{mv.version}.")
                else:
                    self.stdout.write(self.style.WARNING(
                        "No active ModelVersion to persist onto."
                    ))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Could not persist evaluation: {exc}"))
