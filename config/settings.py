
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


# ============================================================
# BASE DIRECTORY & ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in (
        "true", "1", "yes", "on"
    )


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY is missing from .env")

DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = [
    'ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS"',
    '"").split("',
    '")'
]

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "https://digitalgalleria.app,https://www.digitalgalleria.app"
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


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
# DATABASE - SUPABASE POSTGRESQL
# ============================================================

USE_SUPABASE_DATABASE = env_bool(
    "USE_SUPABASE_DATABASE", True
)

if USE_SUPABASE_DATABASE:

    db_host = os.getenv("DB_HOST", "").strip()
    db_name = os.getenv("DB_NAME", "postgres").strip()
    db_user = os.getenv("DB_USER", "").strip()
    db_password = os.getenv("DB_PASSWORD", "")
    db_port = os.getenv("DB_PORT", "6543").strip()

    # Prefer explicit DB_* settings when they are provided.
    if all([db_host, db_name, db_user, db_password]):

        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": db_name,
                "USER": db_user,
                "PASSWORD": db_password,
                "HOST": db_host,
                "PORT": db_port,
                "CONN_MAX_AGE": 0,
                "CONN_HEALTH_CHECKS": True,
                "DISABLE_SERVER_SIDE_CURSORS": True,
                "OPTIONS": {
                    "sslmode": "require",
                },
            }
        }

    else:
        # Optional fallback for hosting platforms using DATABASE_URL.
        database_url = os.getenv("DATABASE_URL", "").strip()

        if not database_url:
            raise ImproperlyConfigured(
                "Supabase database credentials missing. "
                "Check DB_HOST, DB_NAME, DB_USER and DB_PASSWORD."
            )

        DATABASES = {
            "default": dj_database_url.parse(
                database_url,
                conn_max_age=0,
                ssl_require=True,
            )
        }

        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

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
# SUPABASE STORAGE / S3
# ============================================================

USE_SUPABASE_STORAGE = env_bool(
    "USE_SUPABASE_STORAGE", False
)

SUPABASE_URL = os.getenv(
    "SUPABASE_URL", ""
).rstrip("/")

SUPABASE_BUCKET = os.getenv(
    "SUPABASE_BUCKET",
    "digital-galleria-media"
)

SUPABASE_S3_ACCESS_KEY = os.getenv(
    "SUPABASE_S3_ACCESS_KEY", ""
)

SUPABASE_S3_SECRET_KEY = os.getenv(
    "SUPABASE_S3_SECRET_KEY", ""
)

SUPABASE_PROJECT_REF = os.getenv(
    "SUPABASE_PROJECT_REF", ""
).strip()

if not SUPABASE_PROJECT_REF and SUPABASE_URL:
    SUPABASE_PROJECT_REF = (
        SUPABASE_URL
        .replace("https://", "")
        .replace("http://", "")
        .split(".")[0]
    )

SUPABASE_S3_REGION = os.getenv(
    "SUPABASE_S3_REGION",
    "us-east-1"
)

# Supabase S3-compatible endpoint.
SUPABASE_S3_ENDPOINT = os.getenv(
    "SUPABASE_S3_ENDPOINT",
    (
        f"https://{SUPABASE_PROJECT_REF}.storage.supabase.co"
        "/storage/v1/s3"
        if SUPABASE_PROJECT_REF else ""
    )
)

SUPABASE_STORAGE_PUBLIC_URL = (
    f"{SUPABASE_URL}/storage/v1/object/public/"
    f"{SUPABASE_BUCKET}/"
    if SUPABASE_URL else ""
)


# ============================================================
# DJANGO STORAGES
# ============================================================

if USE_SUPABASE_STORAGE:

    if not all([
        SUPABASE_URL,
        SUPABASE_PROJECT_REF,
        SUPABASE_S3_ACCESS_KEY,
        SUPABASE_S3_SECRET_KEY,
        SUPABASE_S3_ENDPOINT,
    ]):
        raise ImproperlyConfigured(
            "Supabase S3 credentials or endpoint are missing."
        )

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
                    f"{SUPABASE_PROJECT_REF}.supabase.co/"
                    f"storage/v1/object/public/{SUPABASE_BUCKET}"
                ),
            },
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }

    MEDIA_URL = SUPABASE_STORAGE_PUBLIC_URL

else:

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }

    MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


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

SECURE_SSL_REDIRECT = env_bool(
    "SECURE_SSL_REDIRECT", not DEBUG
)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# VAPID - WEB PUSH NOTIFICATIONS
# ============================================================

VAPID_PUBLIC_KEY = os.getenv(
    "VAPID_PUBLIC_KEY", ""
)

VAPID_PRIVATE_KEY = os.getenv(
    "VAPID_PRIVATE_KEY", ""
)

VAPID_ADMIN_EMAIL = os.getenv(
    "VAPID_ADMIN_EMAIL",
    os.getenv(
        "VAPID_CLAIMS_EMAIL",
        "mailto:admin@digitalgalleria.app"
    )
)

VAPID_CLAIMS_EMAIL = VAPID_ADMIN_EMAIL
