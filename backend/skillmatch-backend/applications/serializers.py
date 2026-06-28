from rest_framework import serializers

from jobs.serializers import JobSerializer
from .models import Application, RecommendationFeedback


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

    def validate_job(self, job):
        if not job.is_active:
            raise serializers.ValidationError("This job is no longer accepting applications.")
        return job


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationFeedback
        fields = ("id", "job", "signal", "score", "comment", "created_at")
        read_only_fields = ("id", "created_at")
