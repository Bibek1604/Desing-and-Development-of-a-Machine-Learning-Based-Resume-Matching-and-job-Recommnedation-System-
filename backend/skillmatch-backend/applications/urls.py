from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, FeedbackView, SavedJobViewSet

router = DefaultRouter()
router.register("applications", ApplicationViewSet, basename="application")
router.register("saved-jobs",   SavedJobViewSet,   basename="savedjob")

urlpatterns = router.urls + [
    path("feedback/", FeedbackView.as_view(), name="feedback"),
]
