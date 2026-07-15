from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CandidateProfile, EmployerProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.CANDIDATE)

    class Meta:
        model = User
        fields = ("email", "full_name", "password", "role")

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot self-register as admin.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CandidateProfileSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()

    class Meta:
        model = CandidateProfile
        fields = "__all__"
        read_only_fields = ("user", "avatar", "resume_score", "ats_score",
                            "hiring_probability", "updated_at")

    def get_skills(self, obj):
        return [{"id": s.id, "name": s.name, "slug": s.slug} for s in obj.skills.all()]


class EmployerProfileSerializer(serializers.ModelSerializer):
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
