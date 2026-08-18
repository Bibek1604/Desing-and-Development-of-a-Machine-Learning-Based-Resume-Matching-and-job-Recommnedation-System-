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

    # A posting is the direct input to the matching pipeline: an empty or
    # whitespace-only title/description produces an empty TF-IDF vector and a
    # meaningless match score, so both are rejected at the boundary.
    MAX_REQUIRED_SKILLS = 30
    MAX_DESCRIPTION = 20_000

    def validate_title(self, value):
        value = (value or "").strip()
        if len(value) < 3:
            raise serializers.ValidationError("Job title must be at least 3 characters.")
        if len(value) > 200:
            raise serializers.ValidationError("Job title cannot exceed 200 characters.")
        return value

    def validate_description(self, value):
        value = (value or "").strip()
        if len(value) < 20:
            raise serializers.ValidationError(
                "Job description must be at least 20 characters so it can be matched meaningfully."
            )
        if len(value) > self.MAX_DESCRIPTION:
            raise serializers.ValidationError(
                f"Job description cannot exceed {self.MAX_DESCRIPTION:,} characters."
            )
        return value

    def validate_company(self, value):
        return (value or "").strip()

    def validate_required_skill_ids(self, value):
        if len(value) > self.MAX_REQUIRED_SKILLS:
            raise serializers.ValidationError(
                f"A posting cannot require more than {self.MAX_REQUIRED_SKILLS} skills."
            )
        if len({s.pk for s in value}) != len(value):
            raise serializers.ValidationError("Duplicate skills in required_skill_ids.")
        return value

    def validate(self, attrs):
        def current(field):
            return attrs.get(field, getattr(self.instance, field, None))

        smin, smax = current("salary_min"), current("salary_max")
        for field, val in (("salary_min", smin), ("salary_max", smax)):
            if val is not None and val < 0:
                raise serializers.ValidationError({field: "Salary cannot be negative."})
        if smin is not None and smax is not None and smin > smax:
            raise serializers.ValidationError(
                {"salary_min": "Minimum salary cannot be greater than maximum salary."}
            )
        return attrs
