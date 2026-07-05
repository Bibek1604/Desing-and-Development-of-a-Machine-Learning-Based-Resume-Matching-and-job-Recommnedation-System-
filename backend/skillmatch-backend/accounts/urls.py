from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView, MeView, MyProfileView, DeleteAccountView,
    AvatarUploadView, LogoUploadView,
    PasswordResetRequestView, PasswordResetConfirmView,
    SendVerificationEmailView, VerifyEmailConfirmView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Alias kept in sync with the frontend client (lib/api.ts tryRefresh).
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh-alias"),
    path("me/", MeView.as_view(), name="me"),
    path("me/delete/", DeleteAccountView.as_view(), name="delete-account"),
    path("profile/", MyProfileView.as_view(), name="my-profile"),
    path("avatar/", AvatarUploadView.as_view(), name="avatar-upload"),
    path("logo/", LogoUploadView.as_view(), name="logo-upload"),
    # Password reset (request + confirm)
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    # Email verification (send + confirm)
    path("verify-email/send/",    SendVerificationEmailView.as_view(), name="verify-email-send"),
    path("verify-email/confirm/", VerifyEmailConfirmView.as_view(),    name="verify-email-confirm"),
]
