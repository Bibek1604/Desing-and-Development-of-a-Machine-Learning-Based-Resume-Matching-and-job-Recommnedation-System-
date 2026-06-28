from django.conf import settings
from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        REVIEWED = "reviewed", "Reviewed"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    match_score = models.PositiveIntegerField(default=0)
    cover_note = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-applied_at",)
        unique_together = ("candidate", "job")

    def __str__(self):
        return f"{self.candidate.email} -> {self.job.title} ({self.status})"


class RecommendationFeedback(models.Model):
    """Thumbs up/down a candidate gives on a recommended job.

    These signals are the training labels the Phase-7 retraining loop consumes:
    'up' = relevant recommendation, 'down' = not relevant.
    """

    class Signal(models.TextChoices):
        UP = "up", "Relevant"
        DOWN = "down", "Not relevant"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendation_feedback"
    )
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="recommendation_feedback"
    )
    signal = models.CharField(max_length=4, choices=Signal.choices)
    score = models.PositiveIntegerField(
        default=0, help_text="Match score shown to the user when they gave feedback."
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("user", "job")  # one (latest) feedback per user-job

    def __str__(self):
        return f"{self.user.email} {self.signal} job#{self.job_id}"
