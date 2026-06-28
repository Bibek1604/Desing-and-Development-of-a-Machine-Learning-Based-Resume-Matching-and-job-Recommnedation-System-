from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("candidate", "original_filename", "is_primary", "uploaded_at")
    list_filter = ("is_primary",)
    search_fields = ("candidate__email", "original_filename")
    filter_horizontal = ("extracted_skills",)
