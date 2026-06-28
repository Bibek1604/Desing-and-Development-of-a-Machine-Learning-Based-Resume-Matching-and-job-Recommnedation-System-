from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """In-app notification record for a candidate-job match."""

    class Type(models.TextChoices):
        JOB_MATCH      = "job_match",      "Job Match"
        HIGH_PRIORITY  = "high_priority",  "High Priority Match"
        RECRUITER_ALERT= "recruiter_alert","Recruiter Alert"

    candidate        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=20, choices=Type.choices)
    match_score       = models.FloatField()
    match_data        = models.JSONField(
        default=dict,
        help_text="reasons, matched_skills, missing_skills, explanation_summary",
    )
    sent_at    = models.DateTimeField(auto_now_add=True)
    is_read    = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["candidate", "is_read"]),
            models.Index(fields=["candidate", "job"]),
        ]

    def __str__(self):
        return f"{self.candidate.email} | {self.job.title} | {self.match_score:.0f}%"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])


class EmailLog(models.Model):
    """Audit log for every outgoing notification email."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT   = "sent",   "Sent"
        FAILED = "failed", "Failed"

    notification  = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
    )
    recipient      = models.EmailField()
    subject        = models.CharField(max_length=255)
    body           = models.TextField(blank=True)
    status         = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    sent_at        = models.DateTimeField(auto_now_add=True)
    error_message  = models.TextField(blank=True)

    # Analytics tracking
    opened_at   = models.DateTimeField(null=True, blank=True)
    clicked_at  = models.DateTimeField(null=True, blank=True)
    applied_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [models.Index(fields=["recipient", "status"])]

    def __str__(self):
        return f"{self.recipient} | {self.subject} | {self.status}"
