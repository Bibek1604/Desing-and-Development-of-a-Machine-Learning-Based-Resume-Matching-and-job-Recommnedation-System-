"""
Django signals that trigger async match evaluation.

Triggers:
  • Resume saved (post_save)  → evaluate_candidate_matches
  • CandidateProfile saved    → evaluate_candidate_matches
  • Job saved + is_active     → evaluate_job_matches
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _queue(task, *args) -> None:
    """Queue a Celery task without ever blocking the request.

    When NOTIFY_ASYNC is off (local dev without Redis) the dispatch is skipped;
    any unexpected broker error is logged instead of bubbling into the response.
    """
    if not getattr(settings, "NOTIFY_ASYNC", True):
        logger.debug("NOTIFY_ASYNC disabled — skipping %s%r", task.name, args)
        return
    try:
        task.delay(*args)
    except Exception:  # noqa: BLE001 — broker down must never break a request
        logger.exception("Failed to queue %s%r", task.name, args)


# ── Resume upload / update ────────────────────────────────────────────────────
@receiver(post_save, sender="resumes.Resume")
def on_resume_saved(sender, instance, created, **kwargs):
    """Fire match evaluation whenever a resume is saved (new or updated)."""
    from .tasks import evaluate_candidate_matches
    from .models import Notification
    user = instance.candidate
    if user and user.is_active:
        logger.debug("signal: resume saved for %s — queuing match eval", user.email)
        _queue(evaluate_candidate_matches, user.pk)
        Notification.objects.create(
            recipient=user,
            notification_type=Notification.Type.PROFILE_UPDATED,
            match_data={"message": "Resume uploaded and profile analyzed."}
        )


# ── Candidate profile update ──────────────────────────────────────────────────
@receiver(post_save, sender="accounts.CandidateProfile")
def on_profile_saved(sender, instance, created, **kwargs):
    """Re-run matching when a candidate updates their profile / skills."""
    from .tasks import evaluate_candidate_matches
    from .models import Notification
    user = instance.user
    if user and user.is_active:
        logger.debug("signal: profile saved for %s — queuing match eval", user.email)
        _queue(evaluate_candidate_matches, user.pk)
        
        # Don't create too many if just minor updates, but for now we create one.
        Notification.objects.create(
            recipient=user,
            notification_type=Notification.Type.PROFILE_UPDATED,
            match_data={"message": "Profile updated successfully."}
        )


# ── New job posted ────────────────────────────────────────────────────────────
@receiver(post_save, sender="jobs.Job")
def on_job_saved(sender, instance, created, **kwargs):
    """When a new active job is posted, rank all candidates against it."""
    from .tasks import evaluate_job_matches
    if instance.is_active and created:
        logger.debug("signal: new job '%s' posted — queuing candidate eval", instance.title)
        _queue(evaluate_job_matches, instance.pk)
