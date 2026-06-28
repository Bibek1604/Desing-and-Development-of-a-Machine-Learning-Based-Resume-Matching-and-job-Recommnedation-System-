from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "job_type", "location", "is_active", "posted_at")
    list_filter = ("job_type", "is_active")
    search_fields = ("title", "company", "description")
    filter_horizontal = ("required_skills",)
