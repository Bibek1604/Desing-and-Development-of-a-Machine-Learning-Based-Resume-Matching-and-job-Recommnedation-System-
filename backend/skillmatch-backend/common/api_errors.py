"""Domain-specific API exceptions and a guard helper for risky operations.

Raising these gives clients a clear, friendly message while the global
exception handler logs the underlying cause. Using ``guard`` around heavy / I/O
or ML calls keeps view code readable: one wrapper instead of a try/except block
repeated in every endpoint.
"""
from __future__ import annotations

import functools
import logging

from rest_framework.exceptions import APIException
from rest_framework import status

logger = logging.getLogger("skillmatch.api")


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = (
        "This feature is temporarily unavailable. Please try again shortly."
    )
    default_code = "service_unavailable"


class AIServiceError(ServiceUnavailable):
    default_detail = (
        "The AI analysis service is temporarily unavailable. Your data is safe — "
        "please try again in a moment."
    )
    default_code = "ai_service_unavailable"


class ResumeProcessingError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = (
        "We couldn't read this resume. Please upload a valid PDF or DOCX file."
    )
    default_code = "resume_processing_failed"


def guard(*, error=AIServiceError, message: str | None = None, reraise=()):
    """Decorator that converts unexpected exceptions from a callable into a
    clean API error.

    ``reraise`` is a tuple of exception types that should be allowed to bubble
    up untouched (e.g. DRF ``ValidationError`` / ``Http404``) so the global
    handler still returns their proper status codes.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except reraise:
                raise
            except APIException:
                raise
            except Exception as exc:  # noqa: BLE001 — deliberate catch-all
                logger.error(
                    "Guarded operation %s failed: %s",
                    getattr(func, "__qualname__", func),
                    exc,
                    exc_info=exc,
                )
                raise error(message) if message else error()

        return wrapper

    return decorator
