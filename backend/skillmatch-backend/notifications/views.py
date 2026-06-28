from django.db.models import Count, Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, EmailLog
from .serializers import NotificationSerializer, EmailLogSerializer


class NotificationListView(APIView):
    """GET  /api/notifications/         — list candidate's notifications
       POST /api/notifications/read-all/ — mark all as read"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(candidate=request.user).select_related("job")
        ntype = request.query_params.get("type")
        unread = request.query_params.get("unread")
        if ntype:
            qs = qs.filter(notification_type=ntype)
        if unread == "1":
            qs = qs.filter(is_read=False)
        return Response(NotificationSerializer(qs[:50], many=True).data)


class NotificationMarkReadView(APIView):
    """PATCH /api/notifications/<id>/read/  — mark single notification as read"""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, candidate=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        notif.mark_read()
        return Response({"id": notif.pk, "is_read": True})


class NotificationMarkAllReadView(APIView):
    """POST /api/notifications/read-all/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(candidate=request.user, is_read=False).update(is_read=True)
        return Response({"marked_read": updated})


class NotificationUnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(candidate=request.user, is_read=False).count()
        high  = Notification.objects.filter(
            candidate=request.user,
            is_read=False,
            notification_type=Notification.Type.HIGH_PRIORITY,
        ).count()
        return Response({"unread": count, "high_priority": high})


class NotificationAnalyticsView(APIView):
    """GET /api/notifications/analytics/  — recruiter/admin analytics"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Basic stats visible to employer about their job's notifications
        if request.user.role == "employer":
            jobs = request.user.jobs.values_list("id", flat=True)
            total_notifs = Notification.objects.filter(job__in=jobs).count()
            high_prio    = Notification.objects.filter(
                job__in=jobs,
                notification_type=Notification.Type.HIGH_PRIORITY
            ).count()
            emails_sent  = EmailLog.objects.filter(
                notification__job__in=jobs,
                status=EmailLog.Status.SENT,
            ).count()
            emails_failed= EmailLog.objects.filter(
                notification__job__in=jobs,
                status=EmailLog.Status.FAILED,
            ).count()
            return Response({
                "total_notifications": total_notifs,
                "high_priority_matches": high_prio,
                "emails_sent": emails_sent,
                "emails_failed": emails_failed,
            })

        # Candidate's own stats
        total = Notification.objects.filter(candidate=request.user).count()
        unread= Notification.objects.filter(candidate=request.user, is_read=False).count()
        emails= EmailLog.objects.filter(recipient=request.user.email, status=EmailLog.Status.SENT).count()
        return Response({
            "total_notifications": total,
            "unread": unread,
            "emails_received": emails,
        })
