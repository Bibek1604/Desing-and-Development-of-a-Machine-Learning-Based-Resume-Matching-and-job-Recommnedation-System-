from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User, CandidateProfile, EmployerProfile,
    CandidateEmbedding, ATSAnalysis, SkillGapReport, CareerRecommendation
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2"),
        }),
    )


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "location", "resume_score", "ats_score", "hiring_probability", "updated_at")
    search_fields = ("user__email", "headline", "location", "preferred_role")
    list_filter = ("availability", "province")
    filter_horizontal = ("skills",)


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "website", "location", "updated_at")
    search_fields = ("user__email", "company_name", "location")


@admin.register(CandidateEmbedding)
class CandidateEmbeddingAdmin(admin.ModelAdmin):
    list_display = ("user", "model_name", "created_at", "updated_at")
    search_fields = ("user__email", "model_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ATSAnalysis)
class ATSAnalysisAdmin(admin.ModelAdmin):
    list_display = ("resume", "ats_score", "completeness_score", "formatting_score", "keyword_score", "experience_score", "created_at")
    list_filter = ("ats_score",)
    search_fields = ("resume__user__email", "resume__file")
    readonly_fields = ("created_at",)


@admin.register(SkillGapReport)
class SkillGapReportAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "match_improvement_pct", "created_at")
    search_fields = ("user__email", "job__title")
    readonly_fields = ("created_at",)


@admin.register(CareerRecommendation)
class CareerRecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "top_role", "created_at", "updated_at")
    search_fields = ("user__email", "top_role")
    readonly_fields = ("created_at", "updated_at")

