from django.contrib import admin
from .models import Notification, EmailLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ("candidate", "job", "notification_type", "match_score", "is_read", "email_sent", "sent_at")
    list_filter   = ("notification_type", "is_read", "email_sent")
    search_fields = ("candidate__email", "job__title")
    readonly_fields = ("sent_at",)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display  = ("recipient", "subject", "status", "sent_at")
    list_filter   = ("status",)
    search_fields = ("recipient", "subject")
    readonly_fields = ("sent_at",)
