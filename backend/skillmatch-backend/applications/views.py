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
            # Employers see applications to their own jobs.
            return Application.objects.filter(job__employer=user).select_related("job", "candidate")
        return Application.objects.filter(candidate=user).select_related("job")

    def perform_create(self, serializer):
        job = serializer.validated_data["job"]
        if Application.objects.filter(candidate=self.request.user, job=job).exists():
            raise ValidationError("You have already applied to this job.")
        # A scoring failure must not block the application itself — record the
        # application with a zero score and log the problem for later backfill.
        try:
            score = score_candidate_for_job(self.request.user, job)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "score_candidate_for_job failed (job %s)", job.pk, exc_info=exc
            )
            score = 0
        serializer.save(candidate=self.request.user, match_score=score)

    def perform_update(self, serializer):
        """Let the job's employer move an applicant through the pipeline."""
        instance = serializer.instance
        new_status = self.request.data.get("status")
        user = self.request.user
        is_owner_employer = (
            getattr(user, "is_employer", False) and instance.job.employer_id == user.id
        )
        if is_owner_employer and new_status in Application.Status.values:
            serializer.save(status=new_status)
        else:
            serializer.save()


class SavedJobViewSet(viewsets.ModelViewSet):
    """Candidate bookmarks. GET/POST/DELETE only — no PATCH (a bookmark is
    all-or-nothing). Each user sees only their own list."""

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
        serializer.instance = obj  # so the response body reflects the row


class FeedbackView(APIView):
    """POST /api/feedback/  — thumbs up/down on a recommended job.

    Upserts one feedback row per (user, job); re-submitting flips the signal.
    These rows are the labelled signal the retraining loop consumes.
    """
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
