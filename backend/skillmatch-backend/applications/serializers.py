from rest_framework import serializers

from jobs.serializers import JobSerializer
from .models import Application, RecommendationFeedback, SavedJob


class ApplicationSerializer(serializers.ModelSerializer):
    job_detail = JobSerializer(source="job", read_only=True)
    candidate_detail = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            "id", "job", "job_detail", "candidate_detail", "status", "match_score",
            "cover_note", "applied_at",
        )
        read_only_fields = ("status", "match_score", "applied_at")

    def get_candidate_detail(self, obj):
        """Applicant info so the job poster can see who applied."""
        u = obj.candidate
        prof = getattr(u, "candidate_profile", None)
        return {
            "id":         u.id,
            "full_name":  u.full_name,
            "email":      u.email,
            "avatar":     prof.avatar.url if (prof and prof.avatar) else None,
            "degree":     getattr(prof, "degree", "") if prof else "",
            "university": getattr(prof, "university", "") if prof else "",
        }

    MAX_COVER_NOTE = 5_000

    def validate_job(self, job):
        # ``job`` must not be swappable after creation: the stored match_score
        # was computed against the original posting, and reassigning the FK
        # would bypass both the duplicate-application check and the re-score.
        if self.instance is not None and job.pk != self.instance.job_id:
            raise serializers.ValidationError(
                "The job on an existing application cannot be changed. "
                "Withdraw this application and apply to the other role instead."
            )
        if not job.is_active:
            raise serializers.ValidationError("This job is no longer accepting applications.")
        return job

    def validate_cover_note(self, value):
        value = (value or "").strip()
        if len(value) > self.MAX_COVER_NOTE:
            raise serializers.ValidationError(
                f"Cover note cannot exceed {self.MAX_COVER_NOTE:,} characters."
            )
        return value


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationFeedback
        fields = ("id", "job", "signal", "score", "comment", "created_at")
        read_only_fields = ("id", "created_at")


class SavedJobSerializer(serializers.ModelSerializer):
    job_detail = JobSerializer(source="job", read_only=True)

    class Meta:
        model = SavedJob
        fields = ("id", "job", "job_detail", "created_at")
        read_only_fields = ("id", "created_at")
