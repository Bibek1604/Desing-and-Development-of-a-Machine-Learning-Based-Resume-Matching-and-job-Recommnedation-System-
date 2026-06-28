from rest_framework import serializers

from skills.models import Skill
from skills.serializers import SkillSerializer
from .models import Job


class JobSerializer(serializers.ModelSerializer):
    required_skills = SkillSerializer(many=True, read_only=True)
    required_skill_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Skill.objects.all(),
        source="required_skills", required=False,
    )
    job_type_display = serializers.CharField(source="get_job_type_display", read_only=True)
    employer_email = serializers.EmailField(source="employer.email", read_only=True)
    company_logo = serializers.SerializerMethodField()
    # Alias kept for the frontend, which renders job.created_at.
    created_at = serializers.DateTimeField(source="posted_at", read_only=True)

    def get_company_logo(self, obj):
        prof = getattr(obj.employer, "employer_profile", None)
        if prof and prof.logo:
            return prof.logo.url
        return None

    class Meta:
        model = Job
        fields = (
            "id", "title", "company", "description", "requirements", "location",
            "job_type", "job_type_display", "salary_text", "salary_min", "salary_max",
            "required_skills", "required_skill_ids", "company_logo",
            "is_active", "posted_at", "created_at", "employer_email",
        )
        read_only_fields = ("posted_at", "created_at", "employer_email")

    def validate(self, attrs):
        smin = attrs.get("salary_min", getattr(self.instance, "salary_min", None))
        smax = attrs.get("salary_max", getattr(self.instance, "salary_max", None))
        if smin is not None and smax is not None and smin > smax:
            raise serializers.ValidationError(
                {"salary_min": "Minimum salary cannot be greater than maximum salary."}
            )
        return attrs
