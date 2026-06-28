"""Operational endpoints (health checks) used by load balancers / uptime
monitors and by the frontend to detect backend availability."""
from __future__ import annotations

from django.db import connection
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """GET /api/health/ — liveness + database connectivity check.

    Returns 200 when the process is up and the database answers, 503 otherwise.
    Never raises: failures are reported as structured JSON.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # noqa: BLE001 — health check must never throw
            db_ok = False

        status_code = 200 if db_ok else 503
        return Response(
            {
                "status": "ok" if db_ok else "degraded",
                "checks": {"database": "ok" if db_ok else "unavailable"},
            },
            status=status_code,
        )
