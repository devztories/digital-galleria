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


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def env_list(name, default=""):
    value = os.environ.get(name, default)
    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-insecure-key-change-this",
)

DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "*",
)


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [

    # --------------------------------------------------------
    # Django
    # --------------------------------------------------------

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --------------------------------------------------------
    # Third Party
    # --------------------------------------------------------

    "storages",

    # --------------------------------------------------------
    # Digital Galleria Apps
    # --------------------------------------------------------

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

    # Static files
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

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()


# ------------------------------------------------------------
# Option 1:
# DATABASE_URL available
# ------------------------------------------------------------

if DATABASE_URL:

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }


# ------------------------------------------------------------
# Option 2:
# Supabase DB_* variables
# ------------------------------------------------------------

elif os.environ.get("DB_HOST"):

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",

            "NAME": os.environ.get(
                "DB_NAME",
                "postgres",
            ),

            "USER": os.environ.get(
                "DB_USER",
                "postgres",
            ),

            "PASSWORD": os.environ.get(
                "DB_PASSWORD",
                "",
            ),

            "HOST": os.environ.get(
                "DB_HOST",
                "",
            ),

            "PORT": os.environ.get(
                "DB_PORT",
                "5432",
            ),

            "CONN_MAX_AGE": 600,

            "OPTIONS": {
                "sslmode": "require",
            },
        }
    }


# ------------------------------------------------------------
# Option 3:
# Local development SQLite
# ------------------------------------------------------------

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
# SUPABASE CONFIGURATION
# ============================================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "",
).strip().rstrip("/")


SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "",
).strip()


SUPABASE_BUCKET = os.environ.get(
    "SUPABASE_BUCKET",
    "digital-galleria-media",
).strip()


# ============================================================
# SUPABASE S3 CREDENTIALS
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
# SUPABASE PUBLIC MEDIA URL
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
# DJANGO STORAGE
# ============================================================

if SUPABASE_STORAGE_ENABLED:

    STORAGES = {

        # ----------------------------------------------------
        # User uploaded media
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

                # Prevent overwriting files
                "file_overwrite": False,

                # Public bucket
                "querystring_auth": False,

                "default_acl": None,

                # Public URL
                "custom_domain": (
                    f"{SUPABASE_PROJECT_REF}"
                    ".supabase.co"
                    "/storage/v1/object/public/"
                    f"{SUPABASE_BUCKET}"
                ),
            },
        },


        # ----------------------------------------------------
        # Static files
        # ----------------------------------------------------

        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage."
                "CompressedManifestStaticFilesStorage"
            ),
        },
    }


else:

    STORAGES = {

        # ----------------------------------------------------
        # Local media storage
        # ----------------------------------------------------

        "default": {
            "BACKEND": (
                "django.core.files.storage."
                "FileSystemStorage"
            ),
        },


        # ----------------------------------------------------
        # Static files
        # ----------------------------------------------------

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

SECURE_SSL_REDIRECT = env_bool(
    "SECURE_SSL_REDIRECT",
    False,
)


SESSION_COOKIE_SECURE = env_bool(
    "SESSION_COOKIE_SECURE",
    False,
)


CSRF_COOKIE_SECURE = env_bool(
    "CSRF_COOKIE_SECURE",
    False,
)


# ============================================================
# CSRF TRUSTED ORIGINS
# ============================================================

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
)


# ============================================================
# HTTPS / REVERSE PROXY
# ============================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# OPTIONAL SECURITY HEADERS
# ============================================================

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"


# ============================================================
# SESSION SETTINGS
# ============================================================

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"


# ============================================================
# PRODUCTION SECURITY
# ============================================================

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 31536000

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True


# ============================================================
# DIGITAL GALLERIA SETTINGS
# ============================================================

SITE_NAME = "Digital Galleria"


# ============================================================
# DEBUG INFORMATION
# ============================================================

if DEBUG:

    print("---------------------------------------------")
    print("Digital Galleria DEBUG mode enabled")
    print("---------------------------------------------")

    if DATABASE_URL:
        print("Database: DATABASE_URL")

    elif os.environ.get("DB_HOST"):
        print("Database: PostgreSQL / Supabase")

    else:
        print("Database: SQLite")

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

    print(
        "Supabase Storage:",
        "READY"
        if SUPABASE_STORAGE_ENABLED
        else "NOT CONFIGURED",
    )

    print("---------------------------------------------")