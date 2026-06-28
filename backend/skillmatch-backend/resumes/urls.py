from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ResumeViewSet, ResumeAnalyzeView

router = DefaultRouter()
router.register("resumes", ResumeViewSet, basename="resume")

urlpatterns = router.urls + [
    path("resumes/analyze/", ResumeAnalyzeView.as_view(), name="resume-analyze"),
]
