from django.urls import path

from .views import (
    RecommendedJobsView,
    JobCandidatesView,
    SkillGapView,
    CareerRecommendationsView,
    ExplainMatchView,
    AIDashboardView,
    CandidateResumeView,
)

urlpatterns = [
    path("recommendations/",              RecommendedJobsView.as_view(),       name="recommendations"),
    path("jobs/<int:job_id>/candidates/", JobCandidatesView.as_view(),         name="job-candidates"),
    path("candidates/<int:user_id>/resume/", CandidateResumeView.as_view(),    name="candidate-resume"),
    path("skill-gap/<int:job_id>/",       SkillGapView.as_view(),              name="skill-gap"),
    path("career-recommendations/",       CareerRecommendationsView.as_view(), name="career-recommendations"),
    path("explain/<int:job_id>/",         ExplainMatchView.as_view(),          name="explain-match"),
    path("dashboard/",                    AIDashboardView.as_view(),           name="ai-dashboard"),
]
