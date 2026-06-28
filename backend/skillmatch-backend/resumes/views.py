import logging

from rest_framework import viewsets, permissions, parsers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api_errors import AIServiceError
from common.permissions import IsCandidate
from .models import Resume
from .serializers import ResumeSerializer
from .services import process_resume

logger = logging.getLogger("skillmatch.api")


class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        uploaded = serializer.validated_data.get("file")
        is_primary = serializer.validated_data.get("is_primary", False)
        if not Resume.objects.filter(candidate=self.request.user).exists():
            is_primary = True
        if is_primary:
            Resume.objects.filter(
                candidate=self.request.user, is_primary=True
            ).update(is_primary=False)
        resume = serializer.save(
            candidate=self.request.user,
            original_filename=getattr(uploaded, "name", ""),
            is_primary=is_primary,
        )
        # The resume is already persisted. If the parsing / NLP pipeline fails,
        # don't fail the whole upload — log it and let the candidate retry
        # analysis later, so the file they uploaded is never lost.
        try:
            process_resume(resume)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "process_resume failed for resume %s", resume.pk, exc_info=exc
            )

    @action(detail=True, methods=["get"], url_path="ats")
    def ats_analysis(self, request, pk=None):
        """GET /api/resumes/<id>/ats/  ->  ATS analysis for this resume."""
        resume = self.get_object()
        if hasattr(resume, "ats_analysis"):
            a = resume.ats_analysis
            return Response({
                "ats_score":          a.ats_score,
                "completeness_score": a.completeness_score,
                "keyword_score":      a.keyword_score,
                "formatting_score":   a.formatting_score,
                "experience_score":   a.experience_score,
                "strengths":          a.strengths,
                "weaknesses":         a.weaknesses,
                "recommendations":    a.recommendations,
                "section_scores":     a.section_scores,
                "missing_sections":   a.missing_sections,
            })
        # Run on demand if not already computed
        try:
            from .services import _run_ats_analysis
            from skills.models import Skill
            known = list(Skill.objects.values_list("name", flat=True))
            _run_ats_analysis(resume, known)
        except Exception as exc:  # noqa: BLE001
            logger.error("On-demand ATS analysis failed for resume %s", pk, exc_info=exc)
            raise AIServiceError("ATS analysis is temporarily unavailable.")
        if hasattr(resume, "ats_analysis"):
            return self.ats_analysis(request, pk)
        return Response(
            {"detail": "ATS analysis not available."},
            status=status.HTTP_404_NOT_FOUND,
        )


class ResumeAnalyzeView(APIView):
    """POST /api/resumes/analyze/  ->  quick ATS analysis of raw text."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.JSONParser]

    def post(self, request):
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response({"detail": "Provide 'text' in request body."}, status=400)
        if len(text) > 50_000:
            return Response(
                {"detail": "Resume text is too long (50,000 character limit)."},
                status=400,
            )
        try:
            from .services import analyze_resume_text
            result = analyze_resume_text(text)
        except Exception as exc:  # noqa: BLE001
            logger.error("analyze_resume_text failed", exc_info=exc)
            raise AIServiceError("Resume analysis is temporarily unavailable.")
        return Response(result)
