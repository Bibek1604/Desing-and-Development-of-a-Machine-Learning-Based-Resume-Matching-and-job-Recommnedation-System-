"""
Evaluate matcher ranking quality against synthetic ground truth.

Ground truth: a job is "relevant" to a candidate when its title contains the
candidate's preferred_role (e.g. preferred_role="Backend Developer" matches
"Senior Backend Developer"). Reported metrics:

  P@5    — precision in the top 5 recommendations
  Hit@5  — share of candidates with >=1 relevant job in the top 5
  MRR    — mean reciprocal rank of the first relevant job

Usage:
  python manage.py evaluate_matcher --sample 150 --backend tfidf
"""
from __future__ import annotations

import random
import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compute ranking metrics (P@5, Hit@5, MRR) for the matching engine."

    def add_arguments(self, parser):
        parser.add_argument("--sample",  type=int, default=150)
        parser.add_argument("--backend", type=str, default=None)
        parser.add_argument("--k",       type=int, default=5)
        parser.add_argument("--seed",    type=int, default=7)

    def handle(self, *args, **opts):
        from accounts.models import CandidateProfile
        from matching.services import recommend_jobs_for_candidate

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

        p_at_k, hits, rr, evaluated = [], 0, [], 0
        t0 = time.time()
        for profile in sample:
            role = profile.preferred_role.lower()
            recs = recommend_jobs_for_candidate(profile.user, limit=max(k, 10))
            if not recs:
                continue
            evaluated += 1
            top = recs[:k]
            rel = [role in r["job"].title.lower() for r in top]
            p_at_k.append(sum(rel) / k)
            hits += 1 if any(rel) else 0
            first = next((i for i, x in enumerate(rel) if x), None)
            rr.append(1.0 / (first + 1) if first is not None else 0.0)
        elapsed = time.time() - t0

        if not evaluated:
            self.stdout.write(self.style.ERROR("No candidates evaluated."))
            return
        self.stdout.write(self.style.SUCCESS(
            f"backend={opts['backend'] or 'settings default'}  n={evaluated}\n"
            f"P@{k}:   {sum(p_at_k)/len(p_at_k):.3f}\n"
            f"Hit@{k}: {hits/evaluated:.3f}\n"
            f"MRR:   {sum(rr)/len(rr):.3f}\n"
            f"avg latency: {elapsed/evaluated*1000:.0f} ms/candidate"
        ))
