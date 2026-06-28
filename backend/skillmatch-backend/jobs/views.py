from rest_framework import viewsets, permissions

from common.permissions import IsEmployer, IsOwnerOrReadOnly
from .models import Job
from .serializers import JobSerializer


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related("employer").prefetch_related("required_skills")
    serializer_class = JobSerializer
    owner_field = "employer"
    search_fields = ("title", "company", "description", "location")
    filterset_fields = ("job_type", "is_active", "location")
    ordering_fields = ("posted_at", "title")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsEmployer()]
        return [permissions.IsAuthenticated(), IsEmployer(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if self.action == "list":
            # ?mine=true → only the logged-in employer's own postings.
            mine = self.request.query_params.get("mine") in ("1", "true", "True")
            if mine:
                return qs.filter(employer=user) if user.is_authenticated else qs.none()
            # The public (and candidates) only ever see active jobs.
            if not (user.is_authenticated and user.is_employer):
                return qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        company = ""
        profile = getattr(self.request.user, "employer_profile", None)
        if profile is not None:
            company = profile.company_name
        serializer.save(employer=self.request.user, company=company or serializer.validated_data.get("company", ""))
