from django.conf import settings
from django.db import models


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs"
    )
    title = models.CharField(max_length=160)
    company = models.CharField(max_length=160, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=120, blank=True)
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.FULL_TIME
    )
    salary_text = models.CharField(max_length=120, blank=True)
    requirements = models.TextField(blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    required_skills = models.ManyToManyField(
        "skills.Skill", blank=True, related_name="jobs"
    )
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-posted_at",)
        indexes = [
            models.Index(fields=["is_active", "-posted_at"], name="job_active_posted_idx"),
            models.Index(fields=["job_type"], name="job_type_idx"),
            models.Index(fields=["location"], name="job_location_idx"),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company or self.employer.email}"

    def as_match_text(self) -> str:
        """Concatenated text used by the matching engine."""
        skills = " ".join(self.required_skills.values_list("name", flat=True))
        return f"{self.title}. {self.description} {self.requirements} {skills}"
