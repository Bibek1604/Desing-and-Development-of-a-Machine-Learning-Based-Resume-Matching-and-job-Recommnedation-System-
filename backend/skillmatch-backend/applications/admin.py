from django.contrib import admin

from .models import Application, RecommendationFeedback, SavedJob


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "job", "status", "match_score", "applied_at")
    list_filter = ("status",)
    search_fields = ("candidate__email", "job__title")


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "signal", "score", "created_at")
    list_filter = ("signal", "score")
    search_fields = ("user__email", "job__title", "comment")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "created_at")
    search_fields = ("user__email", "job__title")

