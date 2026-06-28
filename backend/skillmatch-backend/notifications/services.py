"""
Notification service: anti-spam guard, smart ranking, email rendering, send pipeline.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    from jobs.models import Job

    User = get_user_model()

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
THRESHOLD_EMAIL       = 80   # send email
THRESHOLD_HIGH_PRIO   = 90   # high-priority email + recruiter alert
THRESHOLD_DASHBOARD   = 60   # show in dashboard only (no email)
MAX_EMAILS_PER_DAY    = 5
SPAM_COOLDOWN_DAYS    = 7
TOP_N_JOBS            = 5


# ── Anti-spam guard ───────────────────────────────────────────────────────────

def _already_notified(user, job) -> bool:
    """Return True if we already emailed this candidate about this job in the last 7 days."""
    from .models import Notification
    cutoff = timezone.now() - timedelta(days=SPAM_COOLDOWN_DAYS)
    return Notification.objects.filter(
        candidate=user,
        job=job,
        email_sent=True,
        sent_at__gte=cutoff,
    ).exists()


def _daily_email_quota_exceeded(user) -> bool:
    """Return True if candidate already received 5+ emails today."""
    from .models import EmailLog
    today = timezone.now().date()
    return EmailLog.objects.filter(
        recipient=user.email,
        status=EmailLog.Status.SENT,
        sent_at__date=today,
    ).count() >= MAX_EMAILS_PER_DAY


def spam_guard(user, job) -> bool:
    """Return True when we SHOULD send (passes all spam checks)."""
    if _already_notified(user, job):
        logger.debug("spam_guard: skip %s / %s — already notified", user.email, job.title)
        return False
    if _daily_email_quota_exceeded(user):
        logger.debug("spam_guard: skip %s — daily quota exceeded", user.email)
        return False
    if not getattr(user, "is_active", True):
        return False
    if not job.is_active:
        return False
    return True


# ── Smart match ranking ───────────────────────────────────────────────────────

def rank_and_filter(matches: list[dict]) -> list[dict]:
    """
    Given a list of {job, score, similarity, matched_skills} dicts,
    return top-N filtered (score>=80) sorted by score → salary → recency → skill count.
    """
    eligible = [m for m in matches if m.get("score", 0) >= THRESHOLD_EMAIL]
    eligible.sort(key=lambda m: (
        -m["score"],
        -(m["job"].salary_max or m["job"].salary_min or 0),
        -(m["job"].created_at.timestamp() if m["job"].created_at else 0),
        -len(m.get("matched_skills", [])),
    ))
    return eligible[:TOP_N_JOBS]


# ── HTML email templates ──────────────────────────────────────────────────────

def _render_match_email(candidate_name: str, job, score: int, match_data: dict,
                        high_priority: bool = False) -> tuple[str, str, str]:
    """Return (subject, text_body, html_body)."""
    reasons    = match_data.get("reasons", [])
    missing    = match_data.get("missing_skills", [])
    matched    = match_data.get("matched_skills", [])
    summary    = match_data.get("explanation_summary", "")
    apply_url  = f"http://localhost:3000/jobs?highlight={job.id}"

    priority_label = "🔴 HIGH PRIORITY " if high_priority else ""
    subject = f"{priority_label}Job Match Found – {score}% Match Score | {job.title}"

    reasons_bullets = "\n".join(f"  ✓ {r}" for r in reasons[:5]) or "  ✓ Strong profile alignment"
    matched_txt     = ", ".join(matched[:6]) or "N/A"
    missing_txt     = ", ".join(missing[:5]) or "None — excellent fit!"

    text_body = f"""
Hello {candidate_name},

{"🔴 HIGH PRIORITY MATCH — Act fast!" if high_priority else "We found a great job match for you!"}

Job Title:    {job.title}
Company:      {job.company}
Location:     {job.location}
Type:         {job.job_type.replace("_", " ").title()}
Match Score:  {score}%

Why It Matches:
{reasons_bullets}

Matched Skills:   {matched_txt}
Missing Skills:   {missing_txt}

{summary}

Apply Here: {apply_url}

Good luck with your application!
— SkillMatch Nepal AI Career Team
""".strip()

    priority_banner = ""
    if high_priority:
        priority_banner = """
        <div style="background:#dc2626;color:white;padding:12px 24px;border-radius:8px;
                    margin-bottom:20px;font-weight:600;font-size:15px;">
          🔴 HIGH PRIORITY MATCH — This role is an excellent fit for your profile!
        </div>"""

    score_color = "#16a34a" if score >= 90 else "#2563eb" if score >= 80 else "#d97706"
    reasons_html = "".join(
        f'<li style="padding:4px 0;color:#166534;">✓ {r}</li>' for r in (reasons[:5] or ["Strong profile alignment"])
    )
    matched_html = "".join(
        f'<span style="background:#dbeafe;color:#1d4ed8;padding:3px 10px;border-radius:99px;'
        f'font-size:13px;margin:3px;display:inline-block;">{s}</span>'
        for s in matched[:6]
    )
    missing_html = "".join(
        f'<span style="background:#fee2e2;color:#991b1b;padding:3px 10px;border-radius:99px;'
        f'font-size:13px;margin:3px;display:inline-block;">{s}</span>'
        for s in missing[:5]
    ) or '<span style="color:#6b7280">None — excellent fit!</span>'

    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:system-ui,-apple-system,sans-serif;background:#f9fafb;margin:0;padding:24px;">
  <div style="max-width:600px;margin:0 auto;background:white;border-radius:16px;
              box-shadow:0 1px 3px rgba(0,0,0,.1);overflow:hidden;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1d4ed8,#7c3aed);padding:32px 32px 24px;">
      <div style="color:white;font-size:22px;font-weight:700;">
        SkillMatch<span style="opacity:.8">Nepal</span>
      </div>
      <div style="color:rgba(255,255,255,.85);font-size:14px;margin-top:4px;">
        AI-Powered Career Matching
      </div>
    </div>

    <!-- Body -->
    <div style="padding:32px;">
      {priority_banner}

      <h2 style="margin:0 0 4px;color:#111827;font-size:20px;">
        Hello {candidate_name},
      </h2>
      <p style="color:#6b7280;margin:0 0 24px;">
        {"Great news! We found a top-tier match for your profile." if high_priority else "We found a new job that closely matches your skills."}
      </p>

      <!-- Job card -->
      <div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <h3 style="margin:0 0 4px;color:#111827;font-size:18px;">{job.title}</h3>
            <p style="margin:0;color:#6b7280;font-size:14px;">
              {job.company} · {job.location} · {job.job_type.replace("_"," ").title()}
            </p>
          </div>
          <div style="text-align:right;flex-shrink:0;margin-left:16px;">
            <div style="font-size:28px;font-weight:700;color:{score_color};">{score}%</div>
            <div style="font-size:12px;color:#9ca3af;">Match Score</div>
          </div>
        </div>
        {f'<p style="margin:12px 0 0;color:#374151;font-size:14px;">{summary}</p>' if summary else ""}
      </div>

      <!-- Why it matches -->
      <div style="margin-bottom:20px;">
        <h4 style="margin:0 0 10px;color:#111827;font-size:15px;">✅ Why It Matches</h4>
        <ul style="margin:0;padding-left:0;list-style:none;">{reasons_html}</ul>
      </div>

      <!-- Matched skills -->
      <div style="margin-bottom:20px;">
        <h4 style="margin:0 0 10px;color:#111827;font-size:15px;">💪 Matched Skills</h4>
        <div>{matched_html}</div>
      </div>

      <!-- Missing skills -->
      <div style="margin-bottom:28px;">
        <h4 style="margin:0 0 10px;color:#111827;font-size:15px;">📚 Skills to Develop</h4>
        <div>{missing_html}</div>
      </div>

      <!-- CTA -->
      <a href="{apply_url}"
         style="display:block;text-align:center;background:linear-gradient(135deg,#2563eb,#7c3aed);
                color:white;padding:14px 24px;border-radius:10px;text-decoration:none;
                font-weight:600;font-size:16px;">
        View Job &amp; Apply →
      </a>

      <p style="text-align:center;margin-top:16px;color:#9ca3af;font-size:12px;">
        You&apos;re receiving this because you uploaded a CV to SkillMatch Nepal.
      </p>
    </div>
  </div>
</body>
</html>
"""
    return subject, text_body, html_body


def _render_recruiter_email(candidate, job, score: int, match_data: dict) -> tuple[str, str, str]:
    """Recruiter alert email."""
    employer = job.employer
    name     = getattr(employer, "full_name", employer.email)
    c_name   = getattr(candidate, "full_name", candidate.email)
    profile  = getattr(candidate, "candidate_profile", None)

    skill_pct  = int(score * 0.95)
    exp_pct    = int(score * 0.88)
    ats_score  = getattr(profile, "ats_score", None)
    degree     = getattr(profile, "degree", "")
    university = getattr(profile, "university", "")
    cgpa       = getattr(profile, "cgpa", None)

    subject = f"[SkillMatch] Top Candidate Alert – {c_name} | {score}% Match for {job.title}"

    text_body = f"""
Recruiter Alert — SkillMatch Nepal

Hello {name},

A highly-qualified candidate has been matched to your job posting.

Candidate: {c_name}
Email:     {candidate.email}
Job:       {job.title}
Match Score:    {score}%
Skills Match:   {skill_pct}%
Experience:     {exp_pct}%
ATS Score:      {ats_score or "N/A"}
Degree:         {degree} {f"from {university}" if university else ""}
CGPA:           {cgpa or "N/A"}

Recommended for immediate review.
— SkillMatch Nepal AI System
""".strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family:system-ui,sans-serif;background:#f9fafb;padding:24px;margin:0;">
  <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;
              box-shadow:0 1px 3px rgba(0,0,0,.1);overflow:hidden;">
    <div style="background:linear-gradient(135deg,#059669,#0284c7);padding:28px 32px 20px;">
      <div style="color:white;font-size:20px;font-weight:700;">SkillMatchNepal</div>
      <div style="color:rgba(255,255,255,.8);font-size:13px;">Recruiter Alert</div>
    </div>
    <div style="padding:28px 32px;">
      <h2 style="margin:0 0 4px;color:#111827;">Hello {name},</h2>
      <p style="color:#6b7280;margin:0 0 20px;">
        A top candidate matches your <strong>{job.title}</strong> posting at a score of
        <strong style="color:#059669">{score}%</strong>.
      </p>

      <div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:20px;">
        <p style="margin:0 0 4px;font-size:18px;font-weight:700;color:#111827;">{c_name}</p>
        <p style="margin:0;color:#6b7280;font-size:14px;">{candidate.email}</p>
        {f'<p style="margin:6px 0 0;color:#374151;font-size:14px;">{degree} · {university} · CGPA {cgpa}</p>' if degree else ""}
      </div>

      <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
        <tr>
          <td style="padding:8px 0;color:#6b7280;font-size:14px;border-bottom:1px solid #f3f4f6;">Overall Match</td>
          <td style="padding:8px 0;font-weight:700;color:#059669;text-align:right;border-bottom:1px solid #f3f4f6;">{score}%</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#6b7280;font-size:14px;border-bottom:1px solid #f3f4f6;">Skills Alignment</td>
          <td style="padding:8px 0;font-weight:600;text-align:right;border-bottom:1px solid #f3f4f6;">{skill_pct}%</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#6b7280;font-size:14px;border-bottom:1px solid #f3f4f6;">Experience Match</td>
          <td style="padding:8px 0;font-weight:600;text-align:right;border-bottom:1px solid #f3f4f6;">{exp_pct}%</td>
        </tr>
        <tr>
          <td style="padding:8px 0;color:#6b7280;font-size:14px;">ATS Score</td>
          <td style="padding:8px 0;font-weight:600;text-align:right;">{ats_score or "N/A"}</td>
        </tr>
      </table>

      <p style="font-weight:600;color:#374151;margin-bottom:6px;">Recommended for review.</p>
      <p style="color:#9ca3af;font-size:12px;margin:0;">
        Log in to SkillMatch Nepal to view the full candidate profile and contact them.
      </p>
    </div>
  </div>
</body>
</html>
"""
    return subject, text_body, html_body


# ── Send pipeline ─────────────────────────────────────────────────────────────

def send_notification_email(notification_id: int) -> bool:
    """Render and send the email for a Notification. Returns True on success."""
    from .models import Notification, EmailLog

    try:
        notif = Notification.objects.select_related("candidate", "job__employer").get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.error("send_notification_email: Notification %s not found", notification_id)
        return False

    user = notif.candidate
    job  = notif.job
    score= int(notif.match_score)
    name = getattr(user, "full_name", user.email.split("@")[0].capitalize())
    high = notif.notification_type == Notification.Type.HIGH_PRIORITY

    subject, text_body, html_body = _render_match_email(name, job, score, notif.match_data, high)

    log = EmailLog.objects.create(
        notification=notif,
        recipient=user.email,
        subject=subject,
        body=html_body,
        status=EmailLog.Status.QUEUED,
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email="noreply@skillmatch.com.np",
            to=[user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()

        log.status = EmailLog.Status.SENT
        log.save(update_fields=["status"])
        notif.email_sent = True
        notif.save(update_fields=["email_sent"])
        logger.info("Email sent: %s → %s", subject[:60], user.email)
        return True

    except Exception as exc:
        log.status = EmailLog.Status.FAILED
        log.error_message = str(exc)
        log.save(update_fields=["status", "error_message"])
        logger.error("Email failed for %s: %s", user.email, exc)
        return False


def send_recruiter_alert_email(notification_id: int) -> bool:
    """Send recruiter alert for a high-priority match."""
    from .models import Notification, EmailLog

    try:
        notif = Notification.objects.select_related("candidate", "job__employer").get(pk=notification_id)
    except Notification.DoesNotExist:
        return False

    employer = notif.job.employer
    if not employer:
        return False

    subject, text_body, html_body = _render_recruiter_email(
        notif.candidate, notif.job, int(notif.match_score), notif.match_data
    )

    log = EmailLog.objects.create(
        notification=notif,
        recipient=employer.email,
        subject=subject,
        body=html_body,
        status=EmailLog.Status.QUEUED,
    )
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email="noreply@skillmatch.com.np",
            to=[employer.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        log.status = EmailLog.Status.SENT
        log.save(update_fields=["status"])
        return True
    except Exception as exc:
        log.status = EmailLog.Status.FAILED
        log.error_message = str(exc)
        log.save(update_fields=["status", "error_message"])
        return False
