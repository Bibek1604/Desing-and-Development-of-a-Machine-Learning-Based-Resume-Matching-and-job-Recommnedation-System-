import os

from rest_framework import serializers

from skills.serializers import SkillSerializer
from .models import Resume

# Only formats resumes.parsing.extract_text can actually read. Anything else
# parses to "" and would silently enter the ML pipeline as an empty document.
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream",  # some browsers send this for .docx
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


class ResumeSerializer(serializers.ModelSerializer):
    extracted_skills = SkillSerializer(many=True, read_only=True)

    def validate_file(self, f):
        if not f:
            raise serializers.ValidationError("A resume file is required.")
        if f.size == 0:
            raise serializers.ValidationError("The uploaded file is empty.")
        if f.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError(
                f"File is too large ({f.size // 1024} KB). Maximum size is 5 MB."
            )
        ext = os.path.splitext(f.name or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext or 'unknown'}'. Upload a PDF, DOCX, DOC or TXT."
            )
        ctype = getattr(f, "content_type", None)
        if ctype and ctype not in ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(f"Unsupported content type '{ctype}'.")
        return f

    class Meta:
        model = Resume
        fields = (
            "id", "file", "original_filename", "raw_text",
            "extracted_skills", "is_primary", "uploaded_at",
        )
        read_only_fields = ("raw_text", "extracted_skills", "uploaded_at", "original_filename")
