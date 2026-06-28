from django.db import models


class ModelVersion(models.Model):
    """A record of each ranking-model training run (blueprint: model_versions).

    The newest active version corresponds to the artifact currently loaded by
    ``ranking_model._get_model``. Kept so the admin can see model history and
    metrics over time, and roll back if needed.
    """
    version = models.PositiveIntegerField(unique=True)
    accuracy = models.FloatField(default=0.0)
    auc = models.FloatField(default=0.0)
    n_samples = models.PositiveIntegerField(default=0)
    n_candidates = models.PositiveIntegerField(default=0)
    positives = models.PositiveIntegerField(default=0)
    negatives = models.PositiveIntegerField(default=0)
    feature_importances = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    trained_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version",)

    def __str__(self):
        return f"ModelVersion v{self.version} (acc={self.accuracy:.2f})"
