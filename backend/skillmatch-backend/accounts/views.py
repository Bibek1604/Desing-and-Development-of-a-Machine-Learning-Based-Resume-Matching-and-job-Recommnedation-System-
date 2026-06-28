from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsCandidate, IsEmployer
from .models import CandidateProfile, EmployerProfile
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CandidateProfileSerializer,
    EmployerProfileSerializer,
)

User = get_user_model()

# Limit profile images to a sensible size (5 MB).
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _save_image(request, profile, field):
    f = request.FILES.get("file")
    if not f:
        return Response({"detail": "No file provided (use form field 'file')."}, status=400)
    if not (f.content_type or "").startswith("image/"):
        return Response({"detail": "Please upload an image file."}, status=400)
    if f.size > MAX_IMAGE_BYTES:
        return Response({"detail": "Image is too large (max 5 MB)."}, status=400)
    setattr(profile, field, f)
    profile.save(update_fields=[field])
    return Response({field: getattr(profile, field).url})


class AvatarUploadView(APIView):
    """POST /api/auth/avatar/  — upload the candidate's profile photo."""
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
        return _save_image(request, profile, "avatar")


class LogoUploadView(APIView):
    """POST /api/auth/logo/  — upload the employer's company logo."""
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        profile, _ = EmployerProfile.objects.get_or_create(user=request.user)
        return _save_image(request, profile, "logo")


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class DeleteAccountView(APIView):
    """DELETE /api/auth/me/delete/  — GDPR right-to-delete.

    Permanently removes the current user and all related data (profile, resumes,
    applications, feedback) via cascading FKs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyProfileView(APIView):
    """Read/update the profile for the current user (candidate or employer)."""

    permission_classes = [permissions.IsAuthenticated]

    def _get_profile_and_serializer(self, user):
        if user.is_candidate:
            profile, _ = CandidateProfile.objects.get_or_create(user=user)
            return profile, CandidateProfileSerializer
        profile, _ = EmployerProfile.objects.get_or_create(user=user)
        return profile, EmployerProfileSerializer

    def get(self, request):
        profile, serializer_cls = self._get_profile_and_serializer(request.user)
        return Response(serializer_cls(profile).data)

    def patch(self, request):
        profile, serializer_cls = self._get_profile_and_serializer(request.user)
        serializer = serializer_cls(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        # The frontend client sends PUT for profile updates; treat it as a
        # lenient full update (same validation path as PATCH).
        return self.patch(request)
