# Celery is optional for local-only runs. If it isn't installed, the app still
# boots — background tasks are simply skipped (NOTIFY_ASYNC defaults off).
try:
    from .celery import app as celery_app  # noqa: F401
except ModuleNotFoundError:
    celery_app = None

__all__ = ("celery_app",)
