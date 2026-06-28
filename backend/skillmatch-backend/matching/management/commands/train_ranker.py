"""Train and save the RandomForest candidate-job ranking model.

Thin CLI wrapper around ``matching.training.train_ranking_model`` (the same
routine the admin 'Retrain' button calls), so there is a single training path.

Usage
-----
  python manage.py train_ranker                 # default sample
  python manage.py train_ranker --samples 1500  # larger / slower / better
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from matching.training import train_ranking_model
from matching.ranking_model import FEATURE_ORDER, MODEL_PATH


class Command(BaseCommand):
    help = "Train and save the RandomForest candidate-job ranking model."

    def add_arguments(self, parser):
        parser.add_argument("--samples", type=int, default=800,
                            help="Number of candidates to sample (each yields up to 12 pairs).")

    def handle(self, *args, **opts):
        try:
            from sklearn.ensemble import RandomForestClassifier  # noqa: F401
            import joblib  # noqa: F401
        except ImportError:
            self.stderr.write("scikit-learn and joblib are required: pip install scikit-learn joblib")
            return

        try:
            m = train_ranking_model(samples=opts["samples"])
        except ValueError as exc:
            self.stderr.write(str(exc))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Trained v{m.get('version')} on {m['n_candidates']} candidates / {m['n_samples']} samples "
            f"(pos={m['positives']}, neg={m['negatives']})"
        ))
        self.stdout.write(f"Test accuracy: {m['accuracy']:.3f} | ROC-AUC: {m['auc']:.3f}")
        self.stdout.write("Feature importances:")
        for name, imp in sorted(m["feature_importances"].items(), key=lambda t: -t[1]):
            self.stdout.write(f"  {name:<16} {imp:.3f}")
        self.stdout.write(self.style.SUCCESS(f"Saved → {MODEL_PATH}"))
