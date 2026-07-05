"""Extended User, CandidateProfile, and EmployerProfile models.

CandidateProfile now carries 25+ fields required by the AI Resume Intelligence
Platform, including district/province, education details, social links,
career preferences, and AI-generated scores.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CANDIDATE = "candidate", "Candidate"
        EMPLOYER = "employer", "Employer"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(
        default=False,
        help_text="Set when the user confirms their address via the verification link.",
    )
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email

    @property
    def is_candidate(self) -> bool:
        return self.role == self.Role.CANDIDATE

    @property
    def is_employer(self) -> bool:
        return self.role == self.Role.EMPLOYER


class CandidateProfile(models.Model):
    """Full candidate profile — original fields + 25 new AI platform fields."""

    class Availability(models.TextChoices):
        IMMEDIATE    = "immediate", "Immediate"
        TWO_WEEKS    = "2_weeks",   "2 Weeks"
        ONE_MONTH    = "1_month",   "1 Month"
        THREE_MONTHS = "3_months",  "3 Months"
        SIX_MONTHS   = "6_months",  "6 Months"

    # ── Original fields ────────────────────────────────────────────────────
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile")
    headline     = models.CharField(max_length=160, blank=True)
    location     = models.CharField(max_length=120, blank=True)
    phone        = models.CharField(max_length=30, blank=True)
    skills       = models.ManyToManyField("skills.Skill", blank=True, related_name="candidates")
    resume_score = models.PositiveIntegerField(default=0)

    # ── Profile photo ───────────────────────────────────────────────────────
    avatar = models.FileField(upload_to="avatars/", blank=True)

    # ── Geography ──────────────────────────────────────────────────────────
    district = models.CharField(max_length=80, blank=True)
    province = models.CharField(max_length=80, blank=True)

    # ── Education ──────────────────────────────────────────────────────────
    degree          = models.CharField(max_length=100, blank=True)
    college         = models.CharField(max_length=160, blank=True)
    university      = models.CharField(max_length=160, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    cgpa            = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # ── Skills & credentials ───────────────────────────────────────────────
    soft_skills    = models.TextField(blank=True, help_text="Comma-separated soft skills")
    certifications = models.TextField(blank=True, help_text="Comma-separated certifications")
    languages      = models.TextField(blank=True, help_text="Comma-separated spoken languages")

    # ── Social / portfolio ─────────────────────────────────────────────────
    github_url    = models.URLField(blank=True)
    linkedin_url  = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # ── Career narrative ───────────────────────────────────────────────────
    resume_summary   = models.TextField(blank=True)
    career_objective = models.TextField(blank=True)
    preferred_role   = models.CharField(max_length=120, blank=True)

    # ── Job preferences ────────────────────────────────────────────────────
    expected_salary_min = models.PositiveIntegerField(null=True, blank=True, help_text="NPR/month")
    expected_salary_max = models.PositiveIntegerField(null=True, blank=True, help_text="NPR/month")
    availability        = models.CharField(max_length=20, choices=Availability.choices, blank=True)
    industry_interest   = models.CharField(max_length=120, blank=True)

    # ── Extra experience fields ────────────────────────────────────────────
    achievement_history  = models.TextField(blank=True)
    volunteer_experience = models.TextField(blank=True)
    research_experience  = models.TextField(blank=True)

    # ── AI scores (set by engine jobs) ────────────────────────────────────
    ats_score          = models.PositiveIntegerField(default=0, help_text="ATS compatibility 0-100")
    hiring_probability = models.FloatField(default=0.0, help_text="Predicted hire probability 0-1")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CandidateProfile<{self.user.email}>"

    def skills_list(self) -> list[str]:
        return list(self.skills.values_list("name", flat=True))

    def soft_skills_list(self) -> list[str]:
        return [s.strip() for s in self.soft_skills.split(",") if s.strip()]

    def certifications_list(self) -> list[str]:
        return [s.strip() for s in self.certifications.split(",") if s.strip()]


class EmployerProfile(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile")
    company_name = models.CharField(max_length=160, blank=True)
    website      = models.URLField(blank=True)
    location     = models.CharField(max_length=120, blank=True)
    description  = models.TextField(blank=True)
    logo         = models.FileField(upload_to="logos/", blank=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"EmployerProfile<{self.user.email}>"


# ── AI-generated artefacts ────────────────────────────────────────────────────

class CandidateEmbedding(models.Model):
    """Sentence-transformer embedding for a candidate's resume text."""
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="embedding")
    vector     = models.TextField(help_text="JSON-encoded float list")
    model_name = models.CharField(max_length=80, default="all-MiniLM-L6-v2")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Embedding<{self.user.email}>"


class ATSAnalysis(models.Model):
    """ATS compatibility analysis result for one resume upload."""
    resume             = models.OneToOneField("resumes.Resume", on_delete=models.CASCADE, related_name="ats_analysis")
    ats_score          = models.PositiveIntegerField(default=0)
    completeness_score = models.PositiveIntegerField(default=0)
    formatting_score   = models.PositiveIntegerField(default=0)
    keyword_score      = models.PositiveIntegerField(default=0)
    experience_score   = models.PositiveIntegerField(default=0)
    strengths          = models.JSONField(default=list)
    weaknesses         = models.JSONField(default=list)
    recommendations    = models.JSONField(default=list)
    section_scores     = models.JSONField(default=dict)
    missing_sections   = models.JSONField(default=list)
    created_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ATSAnalysis<score={self.ats_score}>"


class SkillGapReport(models.Model):
    """Gap analysis between a candidate and a specific job."""
    user                   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="skill_gaps")
    job                    = models.ForeignKey("jobs.Job",  on_delete=models.CASCADE, related_name="skill_gaps")
    missing_skills         = models.JSONField(default=list)
    missing_technologies   = models.JSONField(default=list)
    missing_certifications = models.JSONField(default=list)
    experience_gaps        = models.JSONField(default=list)
    matched_skills         = models.JSONField(default=list)
    match_improvement_pct  = models.FloatField(default=0.0,
                               help_text="Estimated % score improvement if gaps filled")
    created_at             = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")

    def __str__(self):
        return f"SkillGap<{self.user.email} → {self.job.title}>"


class CareerRecommendation(models.Model):
    """Top-10 role recommendations with confidence scores and learning paths."""
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name="career_recommendation")
    recommended_roles = models.JSONField(default=list,
                          help_text='[{"role":"Backend Dev","confidence":0.87,"reason":"..."}]')
    learning_paths    = models.JSONField(default=list,
                          help_text='[{"skill":"Docker","priority":"high","resources":["..."]}]')
    top_role          = models.CharField(max_length=120, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):        return f"CareerRec<{self.user.email}  top={self.top_role}>"

