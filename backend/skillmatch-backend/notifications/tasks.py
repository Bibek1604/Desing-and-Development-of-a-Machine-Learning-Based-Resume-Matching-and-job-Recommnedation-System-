"""
Celery tasks for async match evaluation and email notification.

Task flow:
  resume/profile/job saved
      ↓ signal fires
  evaluate_candidate_matches(user_id)  OR  evaluate_job_matches(job_id)
      ↓ for each match above threshold
  create_and_queue_notification(user_id, job_id, score, match_data)
      ↓ anti-spam check passes
  send_match_email.delay(notification_id)
      ↓ if score >= 90
  send_recruiter_alert.delay(notification_id)
"""
from __future__ import annotations

import logging

try:
    from celery import shared_task
except ModuleNotFoundError:
    # Celery is optional on local-only runs. Provide a no-op decorator so this
    # module imports cleanly; tasks are never dispatched when NOTIFY_ASYNC is off.
    def shared_task(*dargs, **dkwargs):  # type: ignore[misc]
        if len(dargs) == 1 and callable(dargs[0]) and not dkwargs:
            return dargs[0]
        def _wrap(fn):
            return fn
        return _wrap

from django.contrib.auth import get_user_model
from django.db import transaction

from .services import (
    THRESHOLD_DASHBOARD,
    THRESHOLD_EMAIL,
    THRESHOLD_HIGH_PRIO,
    rank_and_filter,
    send_notification_email,
    send_recruiter_alert_email,
    spam_guard,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ── Helper ────────────────────────────────────────────────────────────────────

def _create_notification(user, job, score: float, match_data: dict):
    """Create Notification record inside a transaction. Returns notification or None."""
    from .models import Notification

    if score >= THRESHOLD_HIGH_PRIO:
        ntype = Notification.Type.HIGH_PRIORITY
    else:
        ntype = Notification.Type.JOB_MATCH

    with transaction.atomic():
        notif, created = Notification.objects.get_or_create(
            recipient=user,
            job=job,
            notification_type=ntype,
            defaults={"match_score": score, "match_data": match_data},
        )
        if not created:
            # Update score if higher than stored
            if score > notif.match_score:
                notif.match_score = score
                notif.match_data  = match_data
                notif.save(update_fields=["match_score", "match_data"])
    return notif, created


# ── Core evaluation tasks ─────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=30, name="notifications.evaluate_candidate_matches")
def evaluate_candidate_matches(self, user_id: int):
    """
    Run matching for ALL active jobs for one candidate.
    Called when a candidate uploads/updates their resume or profile.
    """
    from jobs.models import Job
    from matching.services import recommend_jobs_for_candidate

    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        logger.warning("evaluate_candidate_matches: user %s not found", user_id)
        return

    try:
        matches = recommend_jobs_for_candidate(user, limit=50)
    except Exception as exc:
        logger.exception("evaluate_candidate_matches: matching failed for user %s", user_id)
        raise self.retry(exc=exc)

    top = rank_and_filter(matches)
    logger.info("evaluate_candidate_matches: %s — %d eligible matches", user.email, len(top))

    for m in top:
        job   = m["job"]
        score = m["score"]
        data  = {
            "matched_skills":      m.get("matched_skills", []),
            "missing_skills":      m.get("missing_skills", []),
            "reasons":             m.get("reasons", []),
            "explanation_summary": m.get("explanation_summary", ""),
            "similarity":          m.get("similarity", 0),
        }

        if score < THRESHOLD_DASHBOARD:
            continue

        notif, created = _create_notification(user, job, score, data)

        # Only email if score >= threshold and spam guard passes
        if score >= THRESHOLD_EMAIL and spam_guard(user, job):
            send_match_email.delay(notif.pk)
            if score >= THRESHOLD_HIGH_PRIO:
                send_recruiter_alert.delay(notif.pk)


@shared_task(bind=True, max_retries=3, default_retry_delay=30, name="notifications.evaluate_job_matches")
def evaluate_job_matches(self, job_id: int):
    """
    Run matching for ALL active candidates for one newly-posted job.
    Called when a new job is posted or an existing job is re-activated.
    """
    from jobs.models import Job
    from matching.services import rank_candidates_for_job

    try:
        job = Job.objects.get(pk=job_id, is_active=True)
    except Job.DoesNotExist:
        logger.warning("evaluate_job_matches: job %s not found or inactive", job_id)
        return

    try:
        candidates = rank_candidates_for_job(job, limit=200)
    except Exception as exc:
        logger.exception("evaluate_job_matches: ranking failed for job %s", job_id)
        raise self.retry(exc=exc)

    eligible = [c for c in candidates if c.get("score", 0) >= THRESHOLD_EMAIL]
    logger.info("evaluate_job_matches: job '%s' — %d eligible candidates", job.title, len(eligible))

    for c in eligible:
        user  = c.get("user")
        if not user or not user.is_active:
            continue
        score = c["score"]
        data  = {
            "matched_skills":      c.get("matched_skills", []),
            "missing_skills":      c.get("missing_skills", []),
            "reasons":             c.get("reasons", []),
            "explanation_summary": c.get("explanation_summary", ""),
        }

        notif, created = _create_notification(user, job, score, data)

        if spam_guard(user, job):
            send_match_email.delay(notif.pk)
            if score >= THRESHOLD_HIGH_PRIO:
                send_recruiter_alert.delay(notif.pk)


# ── Email sending tasks ───────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="notifications.send_match_email")
def send_match_email(self, notification_id: int):
    """Send job-match email for a Notification record."""
    try:
        success = send_notification_email(notification_id)
        if not success:
            raise Exception(f"Email send returned False for notification {notification_id}")
    except Exception as exc:
        logger.error("send_match_email failed (notif=%s): %s", notification_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="notifications.send_recruiter_alert")
def send_recruiter_alert(self, notification_id: int):
    """Send recruiter alert email for a high-priority Notification."""
    try:
        send_recruiter_alert_email(notification_id)
    except Exception as exc:
        logger.error("send_recruiter_alert failed (notif=%s): %s", notification_id, exc)
        raise self.retry(exc=exc)


# ── Scheduled daily digest ────────────────────────────────────────────────────

@shared_task(name="notifications.daily_match_digest")
def daily_match_digest():
    """
    Periodic task (run via Celery Beat daily at 8 AM Nepal time).
    Re-evaluates all active candidates against all active jobs.
    Only sends emails if the spam guard passes (7-day cooldown).
    """
    logger.info("daily_match_digest: starting")
    active_users = User.objects.filter(is_active=True, role="candidate")
    for user in active_users:
        evaluate_candidate_matches.delay(user.pk)
    logger.info("daily_match_digest: queued %d candidates", active_users.count())
