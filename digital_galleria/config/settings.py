import os
from pathlib import Path

import dj_database_url


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT VARIABLES
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

    # WhiteNoise
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
# SUPABASE POSTGRESQL
# ============================================================

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()


if DATABASE_URL:

    # Preferred for Render if DATABASE_URL is configured
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }

else:

    # --------------------------------------------------------
    # Supabase PostgreSQL using DB_* environment variables
    # --------------------------------------------------------

    DB_NAME = os.environ.get(
        "DB_NAME",
        "postgres",
    )

    DB_USER = os.environ.get(
        "DB_USER",
        "postgres",
    )

    DB_PASSWORD = os.environ.get(
        "DB_PASSWORD",
        "",
    )

    DB_HOST = os.environ.get(
        "DB_HOST",
        "",
    )

    DB_PORT = os.environ.get(
        "DB_PORT",
        "5432",
    )

    if DB_HOST and DB_PASSWORD:

        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",

                "NAME": DB_NAME,
                "USER": DB_USER,
                "PASSWORD": DB_PASSWORD,
                "HOST": DB_HOST,
                "PORT": DB_PORT,

                "CONN_MAX_AGE": 600,

                "OPTIONS": {
                    "sslmode": "require",
                },
            }
        }

    else:

        # Local development fallback
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
# WHITENOISE
# ============================================================

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ============================================================
# SUPABASE CONFIGURATION
# ============================================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "",
).strip().rstrip("/")


SUPABASE_BUCKET = os.environ.get(
    "SUPABASE_BUCKET",
    "digita-galleria-media",
).strip()


# ------------------------------------------------------------
# Supabase S3 credentials
# ------------------------------------------------------------

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
    "ap-south-1",
).strip()


# ============================================================
# SUPABASE PROJECT REFERENCE
# ============================================================

SUPABASE_PROJECT_REF = ""

if SUPABASE_URL:

    SUPABASE_PROJECT_REF = (
        SUPABASE_URL
        .replace("https://", "")
        .replace("http://", "")
        .split(".")[0]
    )


# ============================================================
# SUPABASE S3 ENDPOINT
# ============================================================

if SUPABASE_PROJECT_REF:

    SUPABASE_S3_ENDPOINT = (
        f"https://{SUPABASE_PROJECT_REF}"
        ".storage.supabase.co"
        "/storage/v1/s3"
    )

else:

    SUPABASE_S3_ENDPOINT = ""


# ============================================================
# SUPABASE PUBLIC STORAGE URL
# ============================================================

if SUPABASE_URL and SUPABASE_BUCKET:

    SUPABASE_STORAGE_PUBLIC_URL = (
        f"{SUPABASE_URL}"
        "/storage/v1/object/public/"
        f"{SUPABASE_BUCKET}/"
    )

else:

    SUPABASE_STORAGE_PUBLIC_URL = ""


# ============================================================
# SUPABASE STORAGE ENABLED
# ============================================================

SUPABASE_STORAGE_ENABLED = bool(
    SUPABASE_URL
    and SUPABASE_PROJECT_REF
    and SUPABASE_BUCKET
    and SUPABASE_S3_ACCESS_KEY
    and SUPABASE_S3_SECRET_KEY
)


# ============================================================
# DJANGO FILE STORAGE
# ============================================================

if SUPABASE_STORAGE_ENABLED:

    STORAGES = {

        # ----------------------------------------------------
        # MEDIA / UPLOAD STORAGE
        # ----------------------------------------------------

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

                # Public Supabase Storage URL
                "custom_domain": (
                    f"{SUPABASE_PROJECT_REF}.supabase.co"
                    "/storage/v1/object/public/"
                    f"{SUPABASE_BUCKET}"
                ),
            },
        },

        # ----------------------------------------------------
        # STATIC FILES
        # ----------------------------------------------------

        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }

else:

    # --------------------------------------------------------
    # Local file storage fallback
    # --------------------------------------------------------

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

MEDIA_ROOT = BASE_DIR / "media"


if SUPABASE_STORAGE_ENABLED:

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
# CSRF TRUSTED ORIGINS
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

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# SUPABASE DEBUG STATUS
# ============================================================

if DEBUG:

    print(
        "Digital Galleria DEBUG mode enabled"
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    if DATABASE_URL:

        print(
            "Database: Supabase PostgreSQL "
            "(DATABASE_URL)"
        )

    elif (
        "DATABASES" in globals()
        and DATABASES["default"]["ENGINE"]
        == "django.db.backends.postgresql"
    ):

        print(
            "Database: Supabase PostgreSQL "
            "(DB_* variables)"
        )

    else:

        print(
            "Database: SQLite"
        )

    # --------------------------------------------------------
    # Supabase
    # --------------------------------------------------------

    print(
        "Supabase URL:",
        SUPABASE_URL or "NOT CONFIGURED",
    )

    print(
        "Supabase bucket:",
        SUPABASE_BUCKET or "NOT CONFIGURED",
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

    # --------------------------------------------------------
    # Configuration status
    # --------------------------------------------------------

    print(
        "Supabase configuration:",
        "READY"
        if (
            SUPABASE_URL
            and SUPABASE_BUCKET
        )
        else "INCOMPLETE",
    )

    print(
        "Supabase S3 storage:",
        "READY"
        if SUPABASE_STORAGE_ENABLED
        else "S3 CREDENTIALS NOT CONFIGURED",
    )