from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.views import HealthView

# Project-level error handlers: even requests that never reach a DRF view
# (bad routes, admin, server faults) return safe JSON for API paths.
handler404 = "common.exceptions.json_404"
handler500 = "common.exceptions.json_500"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Operational
    path("api/health/", HealthView.as_view(), name="health"),
    # API
    path("api/auth/",           include("accounts.urls")),
    path("api/",                include("skills.urls")),
    path("api/",                include("resumes.urls")),
    path("api/",                include("jobs.urls")),
    path("api/",                include("applications.urls")),
    path("api/matching/",       include("matching.urls")),
    path("api/notifications/",  include("notifications.urls")),
    path("api/admin/",          include("common.admin_urls")),
    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
