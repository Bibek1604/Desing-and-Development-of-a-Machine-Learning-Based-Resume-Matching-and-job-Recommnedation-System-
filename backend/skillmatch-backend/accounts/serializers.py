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

    def validate_email(self, value):
        # Normalise case so 'A@b.com' and 'a@b.com' cannot become two accounts;
        # the model's unique constraint is case-sensitive on PostgreSQL.
        value = (value or "").strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_full_name(self, value):
        value = (value or "").strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please provide your full name.")
        if len(value) > 150:
            raise serializers.ValidationError("Name cannot exceed 150 characters.")
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

    # ── Field-level validation ────────────────────────────────────────────
    # These fields feed the matching features directly (cgpa_norm, exp_years,
    # preferred_match), so out-of-range values silently distort match scores
    # rather than failing loudly. Bound them at the boundary instead.
    def validate_cgpa(self, value):
        if value is None:
            return value
        if not (0 <= value <= 4):
            raise serializers.ValidationError("CGPA must be between 0.00 and 4.00.")
        return value

    def validate_graduation_year(self, value):
        if value is None:
            return value
        from django.utils import timezone
        this_year = timezone.now().year
        if not (1980 <= value <= this_year + 10):
            raise serializers.ValidationError(
                f"Graduation year must be between 1980 and {this_year + 10}."
            )
        return value

    def validate_phone(self, value):
        import re
        value = (value or "").strip()
        if value and not re.fullmatch(r"[\d\s+()\-]{7,20}", value):
            raise serializers.ValidationError(
                "Phone number may contain digits, spaces and + ( ) - only (7–20 characters)."
            )
        return value

    def validate(self, attrs):
        def current(field):
            return attrs.get(field, getattr(self.instance, field, None))

        lo, hi = current("expected_salary_min"), current("expected_salary_max")
        if lo is not None and hi is not None and lo > hi:
            raise serializers.ValidationError(
                {"expected_salary_min": "Minimum expected salary cannot exceed the maximum."}
            )
        # Free-text fields are concatenated into the candidate document that is
        # vectorised; cap them so one profile cannot dominate the corpus.
        for field, limit in (("resume_summary", 5_000), ("career_objective", 5_000),
                             ("certifications", 2_000), ("soft_skills", 2_000),
                             ("languages", 500), ("achievement_history", 5_000),
                             ("volunteer_experience", 5_000), ("research_experience", 5_000)):
            val = attrs.get(field)
            if val and len(val) > limit:
                raise serializers.ValidationError(
                    {field: f"Cannot exceed {limit:,} characters."}
                )
        return attrs


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
