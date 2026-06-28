"""Cross-cutting request middleware.

* ``RequestIDMiddleware`` attaches a short unique id to every request so that a
  client-visible error can be correlated with a specific server-side log line.
* ``HealthCheckMiddleware`` is intentionally lightweight and lives in
  ``common.views`` instead; see that module.
"""
from __future__ import annotations

import logging
import uuid

logger = logging.getLogger("skillmatch.request")


class RequestIDMiddleware:
    """Generate / propagate an ``X-Request-ID`` for every request."""

    HEADER = "HTTP_X_REQUEST_ID"
    RESPONSE_HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get(self.HEADER)
        request_id = incoming or uuid.uuid4().hex[:12]
        request.request_id = request_id

        response = self.get_response(request)
        response[self.RESPONSE_HEADER] = request_id
        return response
