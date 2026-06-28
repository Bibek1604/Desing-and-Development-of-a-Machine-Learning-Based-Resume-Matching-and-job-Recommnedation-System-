from rest_framework import serializers
from .models import Notification, EmailLog


class NotificationSerializer(serializers.ModelSerializer):
    job_title   = serializers.CharField(source="job.title",   read_only=True)
    job_company = serializers.CharField(source="job.company", read_only=True)
    job_id      = serializers.IntegerField(source="job.id",   read_only=True)

    class Meta:
        model  = Notification
        fields = [
            "id", "job_id", "job_title", "job_company",
            "notification_type", "match_score", "match_data",
            "sent_at", "is_read", "email_sent",
        ]
        read_only_fields = fields


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EmailLog
        fields = ["id", "recipient", "subject", "status", "sent_at", "error_message"]
        read_only_fields = fields
