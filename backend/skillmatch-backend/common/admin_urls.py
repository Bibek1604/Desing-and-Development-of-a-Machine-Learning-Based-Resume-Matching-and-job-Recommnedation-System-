"""Routes for the custom admin panel API, mounted at /api/admin/."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from common.admin_api import (
    AdminUserViewSet,
    AdminJobViewSet,
    AdminApplicationViewSet,
    AdminSkillViewSet,
    AdminResumeViewSet,
    AdminStatsView,
    AdminRetrainView,
    AdminModelVersionView,
    AdminRollbackView,
)

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="admin-user")
router.register("jobs", AdminJobViewSet, basename="admin-job")
router.register("applications", AdminApplicationViewSet, basename="admin-application")
router.register("skills", AdminSkillViewSet, basename="admin-skill")
router.register("resumes", AdminResumeViewSet, basename="admin-resume")

urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("retrain/", AdminRetrainView.as_view(), name="admin-retrain"),
    path("model-versions/", AdminModelVersionView.as_view(), name="admin-model-versions"),
    path("model-versions/rollback/", AdminRollbackView.as_view(), name="admin-model-rollback"),
] + router.urls
