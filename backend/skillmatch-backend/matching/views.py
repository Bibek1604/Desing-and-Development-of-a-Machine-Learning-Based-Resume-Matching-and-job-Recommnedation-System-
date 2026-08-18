"""Matching & AI-intelligence endpoints.

Every endpoint that touches the ML pipeline (TF-IDF / SBERT embeddings, the
ranking model, the skill-gap and career engines) is wrapped so that a failure in
those heavy components degrades to a clean 503 with a friendly message instead
of leaking an internal server error. Validation and 404s still propagate to the
global handler so clients get the correct status codes.
"""
import logging

from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api_errors import AIServiceError
from common.permissions import IsCandidate, IsEmployer
from jobs.models import Job
from .serializers import JobMatchSerializer, CandidateMatchSerializer
from .services import recommend_jobs_for_candidate, rank_candidates_for_job

logger = logging.getLogger("skillmatch.api")


class CandidateResumeView(APIView):
    """GET /api/matching/candidates/<user_id>/resume/

    Lets a job poster (employer) or an admin view a candidate's resume — text
    plus a link to the original file. Candidates cannot use this to read others.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        u = request.user
        is_admin = u.role == "admin" or u.is_staff
        if not (getattr(u, "is_employer", False) or is_admin):
            return Response({"detail": "You do not have permission to view this resume."}, status=403)

        from accounts.models import User
        cand = get_object_or_404(User, pk=user_id)

        # An employer may only read the resume of someone who actually applied
        # to one of their own jobs. Without this check any employer account can
        # enumerate user ids and read every candidate's resume (IDOR).
        if not is_admin:
            from applications.models import Application
            if not Application.objects.filter(
                candidate=cand, job__employer=u
            ).exists():
                return Response(
                    {"detail": "You can only view resumes of candidates who applied to your jobs."},
                    status=403,
                )

        resume = cand.resumes.filter(is_primary=True).first() or cand.resumes.first()
        profile = getattr(cand, "candidate_profile", None)
        return Response({
            "user_id":    cand.pk,
            "full_name":  cand.full_name,
            "email":      cand.email,
            "raw_text":   (resume.raw_text if resume else "") or "",
            "file_url":   (resume.file.url if (resume and resume.file) else None),
            "filename":   (resume.original_filename if resume else ""),
            "skills":     list(profile.skills.values_list("name", flat=True)) if profile else [],
            "degree":     getattr(profile, "degree", "") if profile else "",
            "university": getattr(profile, "university", "") if profile else "",
        })


class RecommendedJobsView(APIView):
    """GET /api/matching/recommendations/  ->  ranked jobs for the current candidate."""
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request):
        try:
            results = recommend_jobs_for_candidate(request.user)
        except Exception as exc:  # noqa: BLE001
            logger.error("recommend_jobs_for_candidate failed", exc_info=exc)
            raise AIServiceError("Job recommendations are temporarily unavailable.")
        return Response(JobMatchSerializer(results, many=True).data)


class JobCandidatesView(APIView):
    """GET /api/matching/jobs/<id>/candidates/  ->  ranked candidates for a job."""
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get(self, request, job_id):
        job = get_object_or_404(Job, pk=job_id)
        if job.employer != request.user:
            return Response(
                {"detail": "You do not own this job."},
                status=403,
            )
        try:
            results = rank_candidates_for_job(job)
        except Exception as exc:  # noqa: BLE001
            logger.error("rank_candidates_for_job failed", exc_info=exc)
            raise AIServiceError("Candidate ranking is temporarily unavailable.")
        return Response(CandidateMatchSerializer(results, many=True).data)


# ── AI Intelligence endpoints ─────────────────────────────────────────────────

class SkillGapView(APIView):
    """GET /api/matching/skill-gap/<job_id>/  ->  skill gap report."""
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request, job_id):
        job = get_object_or_404(Job, pk=job_id, is_active=True)
        try:
            from .skill_gap import SkillGapAnalyzer
            from accounts.models import SkillGapReport

            data = SkillGapAnalyzer().analyze(request.user, job)
            SkillGapReport.objects.update_or_create(
                user=request.user,
                job=job,
                defaults={
                    "missing_skills":         data["missing_skills"],
                    "missing_technologies":   data["missing_technologies"],
                    "missing_certifications": data["missing_certifications"],
                    "experience_gaps":        data["experience_gaps"],
                    "matched_skills":         data["matched_skills"],
                    "match_improvement_pct":  data["match_improvement_pct"],
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("SkillGapAnalyzer failed for job %s", job_id, exc_info=exc)
            raise AIServiceError("Skill-gap analysis is temporarily unavailable.")
        return Response({
            "job_id":    job_id,
            "job_title": job.title,
            "company":   job.company,
            **data,
        })


class CareerRecommendationsView(APIView):
    """GET /api/matching/career-recommendations/  ->  top-10 role recommendations."""
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request):
        try:
            from .career_recommender import CareerRecommendationEngine
            from accounts.models import CareerRecommendation

            result = CareerRecommendationEngine().recommend(request.user)
            CareerRecommendation.objects.update_or_create(
                user=request.user,
                defaults={
                    "recommended_roles": result["recommended_roles"],
                    "learning_paths":    result["learning_paths"],
                    "top_role":          result["top_role"],
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("CareerRecommendationEngine failed", exc_info=exc)
            raise AIServiceError("Career recommendations are temporarily unavailable.")
        return Response(result)


class ExplainMatchView(APIView):
    """GET /api/matching/explain/<job_id>/  ->  explainable AI match breakdown."""
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request, job_id):
        job = get_object_or_404(Job, pk=job_id, is_active=True)
        try:
            from .ranking_model import CandidateJobRanker
            explanation = CandidateJobRanker().explain(request.user, job)
        except Exception as exc:  # noqa: BLE001
            logger.error("CandidateJobRanker.explain failed for job %s", job_id, exc_info=exc)
            raise AIServiceError("Match explanation is temporarily unavailable.")
        return Response({
            "job_id":    job_id,
            "job_title": job.title,
            "company":   job.company,
            **explanation,
        })


class AIDashboardView(APIView):
    """GET /api/matching/dashboard/  ->  full AI intelligence dashboard for candidate.

    Each panel is computed independently and defensively: a failure in one
    section (e.g. the career engine) degrades that panel rather than failing the
    whole dashboard, so the candidate still sees everything that *did* compute.
    """
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request):
        user = request.user
        profile = getattr(user, "candidate_profile", None)

        # ATS data
        ats_data = {}
        try:
            resume = user.resumes.filter(is_primary=True).first() or user.resumes.first()
            if resume and hasattr(resume, "ats_analysis"):
                a = resume.ats_analysis
                ats_data = {
                    "ats_score":          a.ats_score,
                    "completeness_score": a.completeness_score,
                    "keyword_score":      a.keyword_score,
                    "formatting_score":   a.formatting_score,
                    "experience_score":   a.experience_score,
                    "strengths":          a.strengths,
                    "weaknesses":         a.weaknesses,
                    "recommendations":    a.recommendations,
                }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Dashboard ATS panel failed", exc_info=exc)

        # Career recommendations (cached or compute fresh)
        career_data = {"recommended_roles": [], "learning_paths": [], "top_role": ""}
        try:
            career_obj = getattr(user, "career_recommendation", None)
            if career_obj:
                career_data = {
                    "recommended_roles": career_obj.recommended_roles,
                    "learning_paths":    career_obj.learning_paths,
                    "top_role":          career_obj.top_role,
                }
            else:
                from .career_recommender import CareerRecommendationEngine
                career_data = CareerRecommendationEngine().recommend(user)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Dashboard career panel failed", exc_info=exc)

        # Top job matches
        matches_payload = []
        try:
            job_matches = recommend_jobs_for_candidate(user, limit=5)
            matches_payload = [
                {
                    "job_id":        r["job"].pk,
                    "title":         r["job"].title,
                    "company":       r["job"].company,
                    "score":         r["score"],
                    "similarity":    r["similarity"],
                    "matched_skills":r["matched_skills"],
                }
                for r in job_matches
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Dashboard job-matches panel failed", exc_info=exc)

        # Profile summary
        profile_data = {}
        if profile:
            profile_data = {
                "full_name":          user.full_name,
                "email":              user.email,
                "avatar":             profile.avatar.url if profile.avatar else None,
                "degree":             profile.degree,
                "university":         profile.university,
                "cgpa":               float(profile.cgpa) if profile.cgpa else None,
                "skills_count":       profile.skills.count(),
                "ats_score":          profile.ats_score,
                "resume_score":       profile.resume_score,
                "hiring_probability": profile.hiring_probability,
                "preferred_role":     profile.preferred_role,
            }

        return Response({
            "profile":                profile_data,
            "ats_analysis":           ats_data,
            "career_recommendations": career_data,
            "top_job_matches":        matches_payload,
        })
