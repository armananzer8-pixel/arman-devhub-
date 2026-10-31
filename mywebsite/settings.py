
"""
Django settings for mywebsite project.

Day 235 - Security and Deployment Preparation

Local development configuration with environment-based
production settings.
"""
import os
from pathlib import Path
import importlib
from django.core.exceptions import ImproperlyConfigured

# =====================================
# 1. BASE DIRECTORY
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================
# 2. ENVIRONMENT CONFIGURATION
# =====================================

# Development is the default for your local project.
# Set DJANGO_DEBUG=False in production.

DEBUG = os.environ.get(
    "DJANGO_DEBUG", "True"
).strip().lower() == "true"

if not DEBUG and not os.environ.get("DATABASE_URL"):
    raise ImproperlyConfigured(
        "DATABASE_URL must be configured in production."
    )

# =====================================
# 3. SECRET KEY
# =====================================

# Store the secret key outside source code.
# Set DJANGO_SECRET_KEY in your environment.

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is missing. "
        "Set it in your environment before running Django."
    )


# =====================================
# 4. ALLOWED HOSTS
# =====================================

# Local development hosts.
# Production hosts must be explicitly configured.

if DEBUG:
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost",
        "testserver",
    ]
else:
    ALLOWED_HOSTS = [
        host.strip()
        for host in os.environ.get(
            "DJANGO_ALLOWED_HOSTS", ""
        ).split(",")
        if host.strip()
    ]

    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            "DJANGO_ALLOWED_HOSTS must be set "
            "when DEBUG=False."
        )


# =====================================
# 5. APPLICATION DEFINITION
# =====================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "homepage.apps.HomepageConfig",
]


# =====================================
# 6. MIDDLEWARE
# =====================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =====================================
# 7. ROOT URL CONFIGURATION
# =====================================

ROOT_URLCONF = "mywebsite.urls"


# =====================================
# 8. TEMPLATES
# =====================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django.DjangoTemplates"
        ),
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# =====================================
# 9. WSGI APPLICATION
# =====================================

WSGI_APPLICATION = "mywebsite.wsgi.application"


# =====================================
# 10. DATABASE
# =====================================

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    try:
        database_url = importlib.import_module("dj_database_url")
    except ModuleNotFoundError as exc:
        raise ImproperlyConfigured(
            "DATABASE_URL is set, but dj-database-url is not installed."
        ) from exc

    DATABASES = {
        "default": database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# =====================================
# 11. PASSWORD VALIDATION
# =====================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =====================================
# 12. INTERNATIONALIZATION
# =====================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# =====================================
# 13. STATIC FILES
# =====================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
# =====================================
# 14. EMAIL CONFIGURATION
# =====================================

# Print development emails to the terminal.
# Configure a real email provider before deployment.

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
)


# =====================================
# 15. DAY 188 - PRIVATE MEDIA
# =====================================

MEDIA_ROOT = BASE_DIR / "private_media"

MEDIA_URL = "/media/"


# =====================================
# 16. SECURITY SETTINGS
# =====================================

# HTTPS security options are activated only
# when explicitly configured for production.

# Trust HTTPS information from Render's proxy.
# Enable this only when deployed behind Render's trusted proxy.
if not DEBUG and os.environ.get("RENDER") == "true":
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

SECURE_SSL_REDIRECT = (
    not DEBUG
    and os.environ.get(
        "DJANGO_SECURE_SSL_REDIRECT", "False"
    ).lower() == "true"
)

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"


# =====================================
# 17. HSTS CONFIGURATION
# =====================================

# Enable HSTS only after verifying HTTPS
# works correctly for the deployed domain.

SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_HSTS_SECONDS", "0")
) if not DEBUG else 0


# =====================================
# 18. DEFAULT PRIMARY KEY
# =====================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
