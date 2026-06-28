from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from skills.serializers import SkillSerializer
from .models import CandidateProfile, EmployerProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "password")

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot self-register as admin.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class CandidateProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    avatar = serializers.FileField(read_only=True)

    class Meta:
        model = CandidateProfile
        fields = (
            "id", "headline", "location", "phone", "skills", "avatar",
            # Education & background (consumed by the frontend profile client)
            "degree", "college", "university", "graduation_year", "cgpa",
            "district", "province",
            "soft_skills", "certifications", "languages",
            "github_url", "linkedin_url", "portfolio_url",
            "resume_summary", "career_objective", "preferred_role",
            "expected_salary_min", "expected_salary_max", "availability",
            # Computed / ML fields are read-only
            "resume_score", "ats_score", "hiring_probability", "updated_at",
        )
        read_only_fields = ("id", "avatar", "resume_score", "ats_score", "hiring_probability", "updated_at")


class EmployerProfileSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = ("company_name", "website", "location", "description", "logo", "updated_at")
        read_only_fields = ("logo", "updated_at")


class UserSerializer(serializers.ModelSerializer):
    candidate_profile = CandidateProfileSerializer(read_only=True)
    employer_profile = EmployerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "role", "date_joined",
            "candidate_profile", "employer_profile",
        )
        read_only_fields = ("id", "email", "role", "date_joined")
