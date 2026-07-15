import logging

from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsCandidate
from matching.services import score_candidate_for_job
from .models import Application, RecommendationFeedback, SavedJob
from .serializers import ApplicationSerializer, FeedbackSerializer, SavedJobSerializer

logger = logging.getLogger("skillmatch.api")


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsCandidate()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_employer:
            return Application.objects.filter(job__employer=user).select_related("job", "candidate")
        return Application.objects.filter(candidate=user).select_related("job")

    def perform_create(self, serializer):
        job = serializer.validated_data["job"]
        if Application.objects.filter(candidate=self.request.user, job=job).exists():
            raise ValidationError("You have already applied to this job.")
        try:
            score = score_candidate_for_job(self.request.user, job)
        except Exception as exc:  # noqa: BLE001
            logger.error("score_candidate_for_job failed (job %s)", job.pk, exc_info=exc)
            score = 0
        app = serializer.save(candidate=self.request.user, match_score=score)

        from notifications.models import Notification
        Notification.objects.create(
            recipient=job.employer,
            job=job,
            notification_type=Notification.Type.NEW_APPLICATION,
            match_score=score,
            match_data={"candidate_name": self.request.user.full_name or self.request.user.email}
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_status = instance.status
        new_status = self.request.data.get("status")
        user = self.request.user
        is_owner_employer = (
            getattr(user, "is_employer", False) and instance.job.employer_id == user.id
        )
        if is_owner_employer and new_status in Application.Status.values and new_status != old_status:
            serializer.save(status=new_status)
            
            from notifications.models import Notification
            Notification.objects.create(
                recipient=instance.candidate,
                job=instance.job,
                notification_type=Notification.Type.STATUS_UPDATE,
                match_data={"old_status": old_status, "new_status": new_status}
            )
        else:
            serializer.save()


class SavedJobViewSet(viewsets.ModelViewSet):
    """Candidate bookmarks. GET/POST/DELETE only. Each user sees only their own list."""

    serializer_class = SavedJobSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get_queryset(self):
        return (
            SavedJob.objects
            .filter(user=self.request.user)
            .select_related("job")
            .prefetch_related("job__required_skills")
        )

    def perform_create(self, serializer):
        job = serializer.validated_data["job"]
        obj, _created = SavedJob.objects.get_or_create(user=self.request.user, job=job)
        serializer.instance = obj


class FeedbackView(APIView):
    """POST /api/feedback/  — thumbs up/down on a recommended job."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = FeedbackSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj, created = RecommendationFeedback.objects.update_or_create(
            user=request.user,
            job=ser.validated_data["job"],
            defaults={
                "signal":  ser.validated_data["signal"],
                "score":   ser.validated_data.get("score", 0),
                "comment": ser.validated_data.get("comment", ""),
            },
        )
        return Response(
            FeedbackSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
