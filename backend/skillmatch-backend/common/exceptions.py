"""Global error handling for the SkillMatch API.

This module centralises how the backend reports failures so that:

* No raw traceback or internal server error ever reaches an API client.
* Every error response shares one predictable JSON envelope.
* Every unexpected (5xx) failure is logged server-side with full context.

The envelope returned to clients always looks like::

    {
        "error": {
            "code": "validation_error",
            "message": "Human readable summary.",
            "status": 400,
            "details": { ... optional field-level info ... },
            "request_id": "a1b2c3d4"
        }
    }
"""
from __future__ import annotations

import logging

from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("skillmatch.api")


# Maps an HTTP status code to a short machine-readable error code.
_STATUS_CODE_MAP = {
    400: "bad_request",
    401: "authentication_required",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    415: "unsupported_media_type",
    429: "throttled",
    500: "internal_error",
    502: "bad_gateway",
    503: "service_unavailable",
}

GENERIC_500_MESSAGE = (
    "Something went wrong on our end. The issue has been logged and our team "
    "has been notified. Please try again in a moment."
)


def _request_id(context) -> str | None:
    request = (context or {}).get("request") if context else None
    if request is not None:
        return getattr(request, "request_id", None)
    return None


def _build_envelope(*, code, message, status_code, details=None, request_id=None):
    payload = {
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
        }
    }
    if details:
        payload["error"]["details"] = details
    if request_id:
        payload["error"]["request_id"] = request_id
    # Keep a top-level ``detail`` for backwards-compatibility with any client
    # (including DRF's own browsable API) that expects it.
    payload["detail"] = message
    return payload


def _flatten_message(data) -> str:
    """Turn DRF's nested error structure into a single readable sentence."""
    if isinstance(data, dict):
        # Prefer an explicit detail/message key when present.
        for key in ("detail", "message", "error"):
            if key in data and isinstance(data[key], str):
                return data[key]
        parts = []
        for field, value in data.items():
            text = _flatten_message(value)
            if field in ("non_field_errors", "detail"):
                parts.append(text)
            else:
                parts.append(f"{field}: {text}")
        return " ".join(p for p in parts if p)
    if isinstance(data, (list, tuple)):
        return " ".join(_flatten_message(item) for item in data if item)
    return str(data)


def custom_exception_handler(exc, context):
    """DRF ``EXCEPTION_HANDLER`` entry point.

    Handles everything DRF already knows about, then catches *any* remaining
    exception and converts it into a safe 500 response instead of letting
    Django render a debug traceback.
    """
    request_id = _request_id(context)

    # Normalise a few common Django-level exceptions into DRF equivalents so
    # they get the same clean treatment.
    if isinstance(exc, Http404) or isinstance(exc, ObjectDoesNotExist):
        exc = Http404()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = DjangoPermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        # Surface model validation errors as 400s.
        detail = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
        return Response(
            _build_envelope(
                code="validation_error",
                message=_flatten_message(detail),
                status_code=status.HTTP_400_BAD_REQUEST,
                details=detail if isinstance(detail, dict) else None,
                request_id=request_id,
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    response = drf_exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        original = response.data
        details = original if isinstance(original, (dict, list)) else None
        code = "validation_error" if status_code == 400 else _STATUS_CODE_MAP.get(
            status_code, "error"
        )
        message = _flatten_message(original)
        response.data = _build_envelope(
            code=code,
            message=message or "Request could not be completed.",
            status_code=status_code,
            details=details if isinstance(details, dict) else None,
            request_id=request_id,
        )
        if status_code >= 500:
            logger.error(
                "API %s error on %s",
                status_code,
                _path(context),
                exc_info=exc,
                extra={"request_id": request_id},
            )
        return response

    # --- Anything DRF did not recognise -> a safe, logged 500 ---------------
    if isinstance(exc, IntegrityError):
        logger.warning(
            "Database integrity error on %s: %s",
            _path(context), exc, extra={"request_id": request_id},
        )
        return Response(
            _build_envelope(
                code="conflict",
                message="This action conflicts with existing data. It may already exist.",
                status_code=status.HTTP_409_CONFLICT,
                request_id=request_id,
            ),
            status=status.HTTP_409_CONFLICT,
        )

    logger.error(
        "Unhandled exception on %s",
        _path(context),
        exc_info=exc,
        extra={"request_id": request_id},
    )
    return Response(
        _build_envelope(
            code="internal_error",
            message=GENERIC_500_MESSAGE,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _path(context) -> str:
    request = (context or {}).get("request") if context else None
    return getattr(request, "path", "<unknown>") if request else "<unknown>"


# ── Project-level handlers for non-DRF URLs (admin, bad routes, etc.) ─────────
# Registered via ``handler404`` / ``handler500`` in config/urls.py so that even
# requests that never reach a DRF view still return JSON for API paths.

def _wants_json(request) -> bool:
    path = getattr(request, "path", "") or ""
    accept = request.META.get("HTTP_ACCEPT", "") if hasattr(request, "META") else ""
    return path.startswith("/api/") or "application/json" in accept


def json_404(request, exception=None):
    if not _wants_json(request):
        from django.views.defaults import page_not_found
        return page_not_found(request, exception)
    return JsonResponse(
        _build_envelope(
            code="not_found",
            message="The requested resource was not found.",
            status_code=404,
            request_id=getattr(request, "request_id", None),
        ),
        status=404,
    )


def json_500(request):
    logger.error("Server error (500) on %s", getattr(request, "path", "?"))
    if not _wants_json(request):
        from django.views.defaults import server_error
        return server_error(request)
    return JsonResponse(
        _build_envelope(
            code="internal_error",
            message=GENERIC_500_MESSAGE,
            status_code=500,
            request_id=getattr(request, "request_id", None),
        ),
        status=500,
    )
