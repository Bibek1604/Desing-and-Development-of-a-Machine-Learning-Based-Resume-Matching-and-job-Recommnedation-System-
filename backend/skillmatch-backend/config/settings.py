"""Django settings for the SkillMatch Nepal backend."""
from datetime import timedelta
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(key: str, default: str = "0") -> bool:
    return os.environ.get(key, default) == "1"


def env_list(key: str, default: str = "") -> list[str]:
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = env_bool("DEBUG", "1")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Local apps
    "accounts",
    "skills",
    "resumes",
    "jobs",
    "applications",
    "matching",
    "notifications",
]

MIDDLEWARE = [
    "common.middleware.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -------------------------------------------------------------
# This project runs locally on SQLite by default (USE_SQLITE defaults to "1").
# Set USE_SQLITE=0 in the environment if you ever want to point at PostgreSQL.
if env_bool("USE_SQLITE", "1"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "skillmatch"),
            "USER": os.environ.get("DB_USER", "skillmatch"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "skillmatch"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

# --- DRF ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    # Basic API rate limiting. Backed by the configured cache (Redis in
    # production, in-process LocMem in dev). Override via env if needed.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("THROTTLE_ANON", "120/min"),
        "user": os.environ.get("THROTTLE_USER", "600/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Global error handling — every API failure goes through this handler so
    # clients always receive a safe, structured JSON envelope (never a traceback).
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SkillMatch Nepal API",
    "DESCRIPTION": "ML-based resume-to-job matching backend for IT graduates in Nepal.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Group endpoints into friendly categories in Swagger (see common/schema_tags.py).
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "common.schema_tags.categorize_operations",
    ],
    # Controls the order categories appear in the Swagger UI.
    "TAGS": [
        {"name": "System & Operational", "description": "Health check, schema, and docs."},
        {"name": "Authentication & Account", "description": "Register, login, JWT refresh, and profile."},
        {"name": "Skills", "description": "Shared skill vocabulary used by resumes and jobs."},
        {"name": "Resumes", "description": "Resume upload, parsing, skill extraction, and ATS analysis."},
        {"name": "Jobs", "description": "Job postings — public browsing and employer management."},
        {"name": "Applications", "description": "Candidate applications, auto-scored on submit."},
        {"name": "Matching & AI", "description": "Recommendations, skill gaps, and match explanations."},
        {"name": "Notifications", "description": "User notifications and analytics."},
    ],
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3000")

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3000")

# --- Matching engine (upgraded to hybrid SBERT + TF-IDF) ------------------
# Options: "tfidf" | "semantic" | "hybrid"
# tfidf works out of the box; "semantic"/"hybrid" (Sentence-BERT) are opt-in.
MATCHER_BACKEND = os.environ.get("MATCHER_BACKEND", "tfidf")
# Final match score weighting: semantic similarity vs exact skill overlap
MATCH_WEIGHTS = {"similarity": 0.6, "skill_overlap": 0.4}
# Hybrid sub-weights: TF-IDF lexical vs SBERT semantic
MATCHER_HYBRID_WEIGHTS = {"tfidf": 0.30, "semantic": 0.70}

# --- Redis cache ---------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Redis is required in production but optional for local development.
# When USE_REDIS=0 (default while DEBUG=1) the app falls back to an in-memory
# cache, DB-backed sessions, and skips queuing Celery tasks entirely so that
# requests never block on a missing broker.
# Redis is fully optional for now — opt in explicitly with USE_REDIS=1.
USE_REDIS = env_bool("USE_REDIS", "0")

if USE_REDIS:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "TIMEOUT": 60 * 60,
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Gate for signal-driven background match evaluation (notifications/signals.py).
NOTIFY_ASYNC = USE_REDIS

# --- Celery -------------------------------------------------------------------
CELERY_BROKER_URL     = os.environ.get("CELERY_BROKER_URL",     REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT    = ["json"]
CELERY_TASK_SERIALIZER   = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# --- Pagination ---------------------------------------------------------------
REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"] = "common.pagination.StandardPagination"
REST_FRAMEWORK["PAGE_SIZE"] = 20


# ── Notifications app ──────────────────────────────────────────────────────────
# (already added via INSTALLED_APPS below — this section adds email + beat config)

# --- Email backend -----------------------------------------------------------
# Use console backend in dev; switch to SMTP in production via env vars
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST          = os.environ.get("EMAIL_HOST",          "smtp.gmail.com")
EMAIL_PORT          = int(os.environ.get("EMAIL_PORT",      "587"))
EMAIL_USE_TLS       = env_bool("EMAIL_USE_TLS",             "1")
EMAIL_HOST_USER     = os.environ.get("EMAIL_HOST_USER",     "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL  = os.environ.get("DEFAULT_FROM_EMAIL",  "noreply@skillmatch.com.np")

# --- Celery Beat schedule (periodic tasks) -----------------------------------
# Optional: only configured when Celery is installed (skipped on local-only runs).
try:
    from celery.schedules import crontab  # noqa: E402

    CELERY_BEAT_SCHEDULE = {
        # Run daily match digest every day at 08:00 Nepal time
        "daily-match-digest": {
            "task":     "notifications.daily_match_digest",
            "schedule": crontab(hour=8, minute=0),
        },
    }
except ModuleNotFoundError:
    CELERY_BEAT_SCHEDULE = {}

# --- Logging ------------------------------------------------------------------
# All unhandled API errors are logged here with the request id so a client-facing
# error can be traced to a specific server log line. In production point the
# ``file`` handler at a real path or ship logs to your aggregator.
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} [{name}] [req:{request_id}] {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "filters": {
        # Ensures every record has a ``request_id`` attribute even when one was
        # not supplied, so the verbose formatter never raises.
        "request_id": {"()": "common.logging_filters.RequestIDFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "errors.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "filters": ["request_id"],
            "level": "WARNING",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {
            "handlers": ["console", "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "skillmatch": {
            "handlers": ["console", "error_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# --- Production hardening ------------------------------------------------------
# These only activate when DEBUG is off, so local development is unaffected.
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "1")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
    # Fail loudly if someone ships to production with the insecure default key.
    if SECRET_KEY == "dev-insecure-secret-key-change-me":
        raise RuntimeError(
            "SECRET_KEY is using the insecure development default while DEBUG=0. "
            "Set a strong SECRET_KEY environment variable before deploying."
        )
