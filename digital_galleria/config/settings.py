import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT
# ============================================================

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-insecure-key-change-me",
)

DEBUG = os.environ.get(
    "DEBUG",
    "True",
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        "*",
    ).split(",")
    if host.strip()
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "storages",

    # Digital Galleria
    "accounts",
    "categories",
    "products",
    "cart",
    "orders",
    "payments",
    "site_settings",
    "coupons",
    "customization",
    "chatbot",
    "dg_admin",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise for production static files
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

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # Digital Galleria
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
# ============================================================
#
# Local:
#     SQLite is used when DATABASE_URL is not available.
#
# Render / Production:
#     Supabase PostgreSQL is used through DATABASE_URL.
#
# ============================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
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


# WhiteNoise compression/cache support
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ============================================================
# SUPABASE
# ============================================================
#
# Supabase PostgreSQL:
#     DATABASE_URL
#
# Supabase Storage:
#     S3-compatible storage
#
# ============================================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "",
).strip()

SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "",
).strip()

SUPABASE_STORAGE_BUCKET = os.environ.get(
    "SUPABASE_STORAGE_BUCKET",
    "digita-galleria-media",
).strip()

SUPABASE_STORAGE_KEY = os.environ.get(
    "SUPABASE_STORAGE_KEY",
    SUPABASE_KEY,
).strip()

SUPABASE_STORAGE_PUBLIC = (
    os.environ.get(
        "SUPABASE_STORAGE_PUBLIC",
        "True",
    ).lower() == "true"
)


# ============================================================
# SUPABASE STORAGE URLs
# ============================================================

if SUPABASE_URL:
    SUPABASE_STORAGE_URL = (
        f"{SUPABASE_URL.rstrip('/')}"
        "/storage/v1/object"
    )

    SUPABASE_STORAGE_PUBLIC_URL = (
        f"{SUPABASE_URL.rstrip('/')}"
        "/storage/v1/object/public/"
        f"{SUPABASE_STORAGE_BUCKET}/"
    )

    SUPABASE_S3_ENDPOINT = (
        f"{SUPABASE_URL.rstrip('/')}"
        "/storage/v1/s3"
    )
else:
    SUPABASE_STORAGE_URL = ""
    SUPABASE_STORAGE_PUBLIC_URL = ""
    SUPABASE_S3_ENDPOINT = ""


# ============================================================
# SUPABASE S3 CREDENTIALS
# ============================================================
#
# IMPORTANT:
# These are NOT the normal Supabase publishable API key.
#
# Add S3 credentials to .env / Render environment variables:
#
# SUPABASE_S3_ACCESS_KEY=...
# SUPABASE_S3_SECRET_KEY=...
# SUPABASE_S3_REGION=us-east-1
#
# ============================================================

SUPABASE_S3_ACCESS_KEY = os.environ.get(
    "SUPABASE_S3_ACCESS_KEY",
    "",
).strip()

SUPABASE_S3_SECRET_KEY = os.environ.get(
    "SUPABASE_S3_SECRET_KEY",
    "",
).strip()

SUPABASE_S3_REGION = os.environ.get(
    "SUPABASE_S3_REGION",
    "us-east-1",
).strip()


# ============================================================
# SUPABASE STORAGE ENABLED
# ============================================================

SUPABASE_STORAGE_ENABLED = bool(
    SUPABASE_URL
    and SUPABASE_STORAGE_BUCKET
    and SUPABASE_S3_ACCESS_KEY
    and SUPABASE_S3_SECRET_KEY
)


# ============================================================
# DJANGO FILE STORAGE
# ============================================================
#
# If Supabase S3 credentials exist:
#     FileField/ImageField -> Supabase Storage
#
# Otherwise:
#     Local MEDIA_ROOT -> development fallback
#
# ============================================================

if SUPABASE_STORAGE_ENABLED:

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": SUPABASE_S3_ACCESS_KEY,
                "secret_key": SUPABASE_S3_SECRET_KEY,
                "bucket_name": SUPABASE_STORAGE_BUCKET,
                "endpoint_url": SUPABASE_S3_ENDPOINT,
                "region_name": SUPABASE_S3_REGION,
                "addressing_style": "path",
                "file_overwrite": False,
                "querystring_auth": False,
            },
        },

        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }

else:

    STORAGES = {
        "default": {
            "BACKEND": (
                "django.core.files.storage."
                "FileSystemStorage"
            ),
        },

        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }


# ============================================================
# MEDIA FILES
# ============================================================
#
# Local fallback:
#     media/
#
# Supabase:
#     public bucket URL
#
# ============================================================

MEDIA_ROOT = BASE_DIR / "media"

if (
    SUPABASE_STORAGE_ENABLED
    and SUPABASE_STORAGE_PUBLIC
):
    MEDIA_URL = SUPABASE_STORAGE_PUBLIC_URL
else:
    MEDIA_URL = "/media/"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_URL = "accounts:login"

LOGIN_REDIRECT_URL = "home"

LOGOUT_REDIRECT_URL = "home"


# ============================================================
# CLOUDINARY - OPTIONAL
# ============================================================
#
# Supabase Storage has priority.
#
# Cloudinary is only enabled when explicitly configured
# AND Supabase S3 storage is not enabled.
#
# ============================================================

CLOUDINARY_URL = os.environ.get(
    "CLOUDINARY_URL",
    "",
).strip()

if CLOUDINARY_URL and not SUPABASE_STORAGE_ENABLED:

    INSTALLED_APPS += [
        "cloudinary_storage",
        "cloudinary",
    ]

    STORAGES["default"] = {
        "BACKEND": (
            "cloudinary_storage.storage."
            "MediaCloudinaryStorage"
        ),
    }


# ============================================================
# LOW STOCK
# ============================================================

LOW_STOCK_THRESHOLD = int(
    os.environ.get(
        "LOW_STOCK_THRESHOLD",
        "5",
    )
)


# ============================================================
# SECURITY SETTINGS
# ============================================================

SECURE_SSL_REDIRECT = (
    os.environ.get(
        "SECURE_SSL_REDIRECT",
        "False",
    ).lower() == "true"
)

SESSION_COOKIE_SECURE = (
    os.environ.get(
        "SESSION_COOKIE_SECURE",
        "False",
    ).lower() == "true"
)

CSRF_COOKIE_SECURE = (
    os.environ.get(
        "CSRF_COOKIE_SECURE",
        "False",
    ).lower() == "true"
)


# ============================================================
# CSRF / HOST CONFIGURATION
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


# ============================================================
# PROXY / HTTPS
# ============================================================
#
# Useful for Render / reverse proxy deployments.
#
# ============================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# SUPABASE DEBUG STATUS
# ============================================================
#
# These variables are useful for startup diagnostics.
#
# ============================================================

if DEBUG:

    print("Digital Galleria DEBUG mode enabled")

    if DATABASE_URL:
        print("Database: Supabase PostgreSQL")
    else:
        print("Database: SQLite")

    print(
        "Supabase URL:",
        SUPABASE_URL or "NOT CONFIGURED",
    )

    print(
        "Supabase bucket:",
        SUPABASE_STORAGE_BUCKET or "NOT CONFIGURED",
    )

    print(
        "Supabase S3 endpoint:",
        SUPABASE_S3_ENDPOINT or "NOT CONFIGURED",
    )

    print(
        "Supabase public media URL:",
        SUPABASE_STORAGE_PUBLIC_URL
        or "NOT CONFIGURED",
    )

    print(
        "Supabase configuration:",
        "READY"
        if (
            SUPABASE_URL
            and SUPABASE_STORAGE_BUCKET
        )
        else "INCOMPLETE",
    )

    print(
        "Supabase S3 storage:",
        "READY"
        if SUPABASE_STORAGE_ENABLED
        else "S3 CREDENTIALS NOT CONFIGURED",
    )