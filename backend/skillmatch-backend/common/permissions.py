"""Reusable DRF permission classes."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCandidate(BasePermission):
    message = "Only candidate accounts can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_candidate)


class IsEmployer(BasePermission):
    message = "Only employer accounts can perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_employer)


class IsAdmin(BasePermission):
    """Full-access role for the custom admin panel.

    Accepts either the ``admin`` role or any staff/superuser account so the
    Django superuser created by ``seed_admin`` can use the panel too.
    """

    message = "Admin access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == "admin" or user.is_staff or user.is_superuser)
        )


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: read for anyone, write only for the owner.

    Set `owner_field` on the view (defaults to "employer") to control which
    attribute identifies the owning user.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner_field = getattr(view, "owner_field", "employer")
        return getattr(obj, owner_field, None) == request.user
