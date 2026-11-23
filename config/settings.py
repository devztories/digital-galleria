
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-development-only-key"
)

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in (
    "true", "1", "yes"
)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "digitalgalleria.app",
    "www.digitalgalleria.app",
    ".vercel.app",
]

extra_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")

if extra_hosts:
    ALLOWED_HOSTS.extend(
        host.strip()
        for host in extra_hosts.split(",")
        if host.strip()
    )


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "storages",

    "accounts",
    "categories",
    "products",
    "cart",
    "orders",
    "payments",
    "site_settings",
    "coupons",
    "customization",
    "dg_admin",
    "notifications",
]


# ============================================================
# MIDDLEWARE
# ============================================================

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


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "config.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_context",
                "site_settings.context_processors.site_settings_context",
            ],
        },
    },
]


# ============================================================
# WSGI / ASGI
# ============================================================

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ============================================================
# DATABASE
# Local: SQLite
# Vercel: Supabase PostgreSQL
# ============================================================

if os.getenv("VERCEL") == "1":

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is missing in Vercel environment variables"
        )

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            ssl_require=True,
        )
    }

else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# CUSTOM USER MODEL
# ============================================================

AUTH_USER_MODEL = "accounts.User"


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = []


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================================
# SUPABASE STORAGE CONFIGURATION
# ============================================================

USE_SUPABASE_STORAGE = (
    os.getenv("USE_SUPABASE_STORAGE", "False").lower()
    in ("true", "1", "yes")
)

SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://YOUR_PROJECT_REF.supabase.co"
)

SUPABASE_BUCKET = os.getenv(
    "SUPABASE_BUCKET",
    "digita-galleria-media"
)

SUPABASE_S3_ACCESS_KEY = os.getenv(
    "SUPABASE_S3_ACCESS_KEY",
    ""
)

SUPABASE_S3_SECRET_KEY = os.getenv(
    "SUPABASE_S3_SECRET_KEY",
    ""
)

SUPABASE_S3_REGION = os.getenv(
    "SUPABASE_S3_REGION",
    "us-east-1"
)


# ============================================================
# SUPABASE STORAGE URLS
# ============================================================

SUPABASE_PROJECT_REF = (
    SUPABASE_URL
    .replace("https://", "")
    .replace("http://", "")
    .split(".")[0]
)

SUPABASE_S3_ENDPOINT = (
    f"https://{SUPABASE_PROJECT_REF}.storage.supabase.co/storage/v1/s3"
)

SUPABASE_STORAGE_PUBLIC_URL = (
    f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/"
)


# ============================================================
# DJANGO STORAGES
# ============================================================

if USE_SUPABASE_STORAGE:

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": SUPABASE_S3_ACCESS_KEY,
                "secret_key": SUPABASE_S3_SECRET_KEY,
                "bucket_name": SUPABASE_BUCKET,
                "endpoint_url": SUPABASE_S3_ENDPOINT,
                "region_name": SUPABASE_S3_REGION,
                "addressing_style": "path",
                "file_overwrite": False,
                "querystring_auth": False,
                "default_acl": None,
                "custom_domain": (
                    f"{SUPABASE_PROJECT_REF}.supabase.co"
                    f"/storage/v1/object/public/{SUPABASE_BUCKET}"
                ),
            },
        },

        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    MEDIA_URL = SUPABASE_STORAGE_PUBLIC_URL

else:

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },

        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    MEDIA_URL = "/media/"


MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# WHITENOISE
# ============================================================

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"


# ============================================================
# LOW STOCK
# ============================================================

LOW_STOCK_THRESHOLD = 5


# ============================================================
# SECURITY SETTINGS
# ============================================================

SECURE_SSL_REDIRECT = (
    not DEBUG and os.getenv("VERCEL") != "1"
)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://digitalgalleria.app",
    "https://www.digitalgalleria.app",
]

extra_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")

if extra_origins:
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip()
        for origin in extra_origins.split(",")
        if origin.strip()
    )


# ============================================================
# PROXY / HTTPS
# ============================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# ADMIN WEB PUSH (VAPID)
# ============================================================

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")

VAPID_ADMIN_EMAIL = os.getenv(
    "VAPID_ADMIN_EMAIL",
    "mailto:digitalgalleria2024@gmail.com"
)
