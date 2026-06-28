from django.conf import settings
from django.db import models


class Resume(models.Model):
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes"
    )
    file = models.FileField(upload_to="resumes/")
    original_filename = models.CharField(max_length=255, blank=True)
    raw_text = models.TextField(blank=True)
    extracted_skills = models.ManyToManyField(
        "skills.Skill", blank=True, related_name="resumes"
    )
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self):
        return f"Resume<{self.candidate.email}:{self.original_filename}>"
