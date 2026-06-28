"""Custom admin-panel API.

Exposes full CRUD over every major resource (users, jobs, applications,
skills, resumes) plus aggregate stats, all gated behind the IsAdmin
permission. Consumed by the Next.js /admin section.
"""
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from common.permissions import IsAdmin
from common.concurrency import run_parallel
from accounts.models import CandidateProfile, EmployerProfile
from jobs.models import Job
from jobs.serializers import JobSerializer
from applications.models import Application
from applications.serializers import ApplicationSerializer
from skills.models import Skill
from skills.serializers import SkillSerializer
from resumes.models import Resume
from resumes.serializers import ResumeSerializer

User = get_user_model()


# ── Users ──────────────────────────────────────────────────────────────────
class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, validators=[validate_password]
    )
    skills_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "role",
            "is_active", "is_staff", "date_joined", "password", "skills_count",
        )
        read_only_fields = ("id", "date_joined")

    def get_skills_count(self, obj):
        prof = getattr(obj, "candidate_profile", None)
        return prof.skills.count() if prof else 0

    def create(self, validated_data):
        password = validated_data.pop("password", "") or secrets.token_urlsafe(12)
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", "")
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().order_by("-date_joined")
    filterset_fields = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    ordering_fields = ("date_joined", "email", "role")


# ── Jobs ───────────────────────────────────────────────────────────────────
class AdminJobViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = JobSerializer
    queryset = Job.objects.select_related("employer").prefetch_related("required_skills").all()
    search_fields = ("title", "company", "description", "location")
    filterset_fields = ("job_type", "is_active")
    ordering_fields = ("posted_at", "title")

    def perform_create(self, serializer):
        # Admin-created jobs are owned by the admin unless an employer exists.
        serializer.save(employer=self.request.user)


# ── Applications ───────────────────────────────────────────────────────────
class AdminApplicationSerializer(ApplicationSerializer):
    """Like ApplicationSerializer but lets admins edit the status."""
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)

    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ("candidate_email",)
        read_only_fields = ("match_score", "applied_at")  # status now writable


class AdminApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = AdminApplicationSerializer
    queryset = Application.objects.select_related("job", "candidate").all()
    filterset_fields = ("status",)
    search_fields = ("candidate__email", "job__title")
    ordering_fields = ("applied_at", "match_score", "status")


# ── Skills ─────────────────────────────────────────────────────────────────
class AdminSkillViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = SkillSerializer
    queryset = Skill.objects.all()
    search_fields = ("name", "category")
    ordering_fields = ("name", "category")


# ── Resumes ────────────────────────────────────────────────────────────────
class AdminResumeSerializer(ResumeSerializer):
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)

    class Meta(ResumeSerializer.Meta):
        fields = ResumeSerializer.Meta.fields + ("candidate_email",)


class AdminResumeViewSet(viewsets.ModelViewSet):
    """List / retrieve / delete resumes (admins don't upload on a user's behalf)."""
    http_method_names = ["get", "delete", "head", "options"]
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = AdminResumeSerializer
    queryset = Resume.objects.select_related("candidate").prefetch_related("extracted_skills").all()
    search_fields = ("candidate__email", "original_filename")
    ordering_fields = ("uploaded_at",)


# ── Stats ──────────────────────────────────────────────────────────────────
class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        # Each count is an independent read — run them concurrently on a thread
        # pool so the dashboard responds in roughly one query's time, not ten.
        r = run_parallel({
            "users_total":      lambda: User.objects.count(),
            "users_candidates": lambda: User.objects.filter(role="candidate").count(),
            "users_employers":  lambda: User.objects.filter(role="employer").count(),
            "users_admins":     lambda: User.objects.filter(role="admin").count(),
            "users_active":     lambda: User.objects.filter(is_active=True).count(),
            "jobs_total":       lambda: Job.objects.count(),
            "jobs_active":      lambda: Job.objects.filter(is_active=True).count(),
            "applications":     lambda: Application.objects.count(),
            "skills":           lambda: Skill.objects.count(),
            "resumes":          lambda: Resume.objects.count(),
        })
        n = lambda key: r.get(key) or 0  # noqa: E731 — coalesce a failed task to 0
        return Response({
            "users": {
                "total":      n("users_total"),
                "candidates": n("users_candidates"),
                "employers":  n("users_employers"),
                "admins":     n("users_admins"),
                "active":     n("users_active"),
            },
            "jobs": {
                "total":  n("jobs_total"),
                "active": n("jobs_active"),
            },
            "applications": n("applications"),
            "skills":       n("skills"),
            "resumes":      n("resumes"),
        })


# ── Model versioning + one-click retrain ─────────────────────────────────────
class AdminRetrainView(APIView):
    """POST /api/admin/retrain/  — retrain the ranking model on current data."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        try:
            samples = int(request.data.get("samples", 800))
        except (TypeError, ValueError):
            samples = 800
        from matching.training import train_ranking_model
        try:
            metrics = train_ranking_model(samples=samples)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001
            return Response({"detail": f"Training failed: {exc}"}, status=503)
        return Response(metrics, status=200)


class AdminModelVersionView(APIView):
    """GET /api/admin/model-versions/  — training-run history."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            from matching.models import ModelVersion
            data = [{
                "version": mv.version, "accuracy": mv.accuracy, "auc": mv.auc,
                "n_samples": mv.n_samples, "n_candidates": mv.n_candidates,
                "positives": mv.positives, "negatives": mv.negatives,
                "feature_importances": mv.feature_importances,
                "is_active": mv.is_active, "trained_at": mv.trained_at,
            } for mv in ModelVersion.objects.all()[:20]]
        except Exception:  # noqa: BLE001 — table may not be migrated yet
            data = []
        return Response(data)


class AdminRollbackView(APIView):
    """POST /api/admin/model-versions/rollback/  — activate a previous version."""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        try:
            version = int(request.data.get("version"))
        except (TypeError, ValueError):
            return Response({"detail": "A numeric 'version' is required."}, status=400)
        from matching.training import rollback_to_version
        try:
            result = rollback_to_version(version)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001
            return Response({"detail": f"Rollback failed: {exc}"}, status=503)
        return Response(result)
