from rest_framework import serializers
from .models import Notification, EmailLog


class NotificationSerializer(serializers.ModelSerializer):
    job_title   = serializers.SerializerMethodField()
    job_company = serializers.SerializerMethodField()
    job_id      = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = [
            "id", "job_id", "job_title", "job_company",
            "notification_type", "match_score", "match_data",
            "sent_at", "is_read", "email_sent",
        ]
        read_only_fields = fields

    def get_job_title(self, obj):
        if obj.job:
            return obj.job.title
        if obj.notification_type == Notification.Type.PROFILE_UPDATED:
            return "Profile Update"
        return "System Notification"

    def get_job_company(self, obj):
        if obj.job:
            return obj.job.company
        return "SkillMatch"

    def get_job_id(self, obj):
        return obj.job.id if obj.job else None


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmailLog
        fields = ["id", "recipient", "subject", "status", "sent_at", "error_message"]
        read_only_fields = fields
