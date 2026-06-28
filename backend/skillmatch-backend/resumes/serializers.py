from rest_framework import serializers

from skills.serializers import SkillSerializer
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    extracted_skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = Resume
        fields = (
            "id", "file", "original_filename", "raw_text",
            "extracted_skills", "is_primary", "uploaded_at",
        )
        read_only_fields = ("raw_text", "extracted_skills", "uploaded_at", "original_filename")
