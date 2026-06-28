"""Fairness / bias audit (blueprint Step 2.4 — Fairness & Bias Testing).

Measures whether the recommendation engine treats candidate groups fairly. For
a sample of candidates it computes each candidate's best job-match score, groups
candidates by college and by province, and reports per-group:

  • representation   — share of the sampled population
  • avg top score    — mean best-match score
  • success rate     — fraction reaching a 'strong match' threshold

It then applies the **80% rule (disparate impact)**: if any group's success rate
is below 80% of the best-performing group's rate, it is flagged.

Usage
-----
  python manage.py bias_audit --sample 500 --threshold 50
"""
from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand

from accounts.models import CandidateProfile
from matching.services import recommend_jobs_for_candidate


class Command(BaseCommand):
    help = "Run a fairness / demographic-parity audit over recommendations."

    def add_arguments(self, parser):
        parser.add_argument("--sample", type=int, default=500,
                            help="Number of candidates to evaluate.")
        parser.add_argument("--threshold", type=int, default=50,
                            help="Score (0-100) considered a 'strong match'.")
        parser.add_argument("--min-group", type=int, default=10,
                            help="Ignore groups smaller than this in parity flags.")

    def handle(self, *args, **opts):
        thr = opts["threshold"]
        profiles = list(
            CandidateProfile.objects.select_related("user")
            .prefetch_related("user__resumes", "skills")[: opts["sample"]]
        )
        if not profiles:
            self.stderr.write("No candidates found. Seed data first (seed_dataset_v3).")
            return

        # (top_score, hit?) per candidate, plus group keys.
        by_college = defaultdict(list)
        by_province = defaultdict(list)
        evaluated = 0
        for p in profiles:
            try:
                recs = recommend_jobs_for_candidate(p.user, limit=5)
            except Exception:  # noqa: BLE001
                continue
            top = recs[0]["score"] if recs else 0
            hit = 1 if top >= thr else 0
            by_college[(p.college or "Unknown").strip() or "Unknown"].append((top, hit))
            by_province[(p.province or "Unknown").strip() or "Unknown"].append((top, hit))
            evaluated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nFairness audit over {evaluated} candidates (strong-match threshold = {thr})"
        ))
        self._report("BY PROVINCE", by_province, opts["min_group"])
        self._report("BY COLLEGE (top 12 groups)", by_college, opts["min_group"], top_n=12)

    def _report(self, title, groups, min_group, top_n=None):
        rows = []
        for key, vals in groups.items():
            n = len(vals)
            avg = sum(v[0] for v in vals) / n
            rate = sum(v[1] for v in vals) / n
            rows.append((key, n, avg, rate))
        rows.sort(key=lambda r: -r[1])  # by group size
        if top_n:
            rows = rows[:top_n]

        eligible = [r for r in rows if r[1] >= min_group]
        best_rate = max((r[3] for r in eligible), default=0.0) or 1e-9

        self.stdout.write(f"\n=== {title} ===")
        self.stdout.write(f"{'Group':<34}{'N':>6}{'Repr%':>8}{'AvgTop':>8}{'Success':>9}{'Parity':>9}")
        total = sum(r[1] for r in rows)
        flagged = 0
        for key, n, avg, rate in rows:
            parity = rate / best_rate if n >= min_group else float("nan")
            flag = ""
            if n >= min_group and parity < 0.80:
                flag = "  ⚠ below 80%"
                flagged += 1
            repr_pct = 100 * n / total if total else 0
            par_txt = "n/a" if parity != parity else f"{parity*100:4.0f}%"
            self.stdout.write(
                f"{key[:33]:<34}{n:>6}{repr_pct:>7.1f}%{avg:>8.1f}{rate*100:>8.0f}%{par_txt:>9}{flag}"
            )
        if flagged:
            self.stdout.write(self.style.WARNING(
                f"{flagged} group(s) below the 80% parity threshold — investigate before retraining."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("All eligible groups within the 80% parity threshold."))
