import os
from datetime import timedelta
from corsheaders.defaults import default_headers
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = str(os.environ.get("DJANGO_DEBUG")) == "1"

# -------------------------------------------------
# ------------- CORS SETTINGS ---------------------
# -------------------------------------------------

# Allow credentials to be sent in cross-origin requests
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
]

# Allow cookies to be sent
CORS_ALLOW_CREDENTIALS = True


CORS_ALLOW_HEADERS = list(default_headers) + [
    "X-Origin",
]

# -------------------------------------------------
# ------------- CUSTOM SETTINGS -------------------
# -------------------------------------------------

# To determine where request is coming from.
# For this case, my react app is running from this localhost
X_ORIGIN_HOST: str = str(os.environ.get("GOOGLE_CLIENT_SECRET"))
X_ORIGIN_ACTIVATE_ACCOUNT_PATH: str = str(os.environ.get("GOOGLE_CLIENT_SECRET"))


# -------------------------------------------------
# ------------- DJANGO SETTINGS -------------------
# -------------------------------------------------

CSRF_TRUSTED_ORIGINS = ["https://*.ngrok-free.app"]
# Django has a setting called SECURE_PROXY_SSL_HEADER which tells
# it to properly detect the protocol when the app is running
# behind a proxy (e.g., Ngrok, AWS ELB, etc.).
# [FOR request.build_absolute_uri(key_path) TO CREATE PROPER URLS]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Set secure cookie parameters
SESSION_COOKIE_SECURE = not DEBUG  # Ensure cookies are only sent over HTTPS
CSRF_COOKIE_SECURE = not DEBUG


# -------------------------------------------------
# ------------- GOOGLE SETTINGS -------------------
# -------------------------------------------------
GOOGLE_CLIENT_ID = str(os.environ.get("GOOGLE_CLIENT_ID"))
GOOGLE_CLIENT_SECRET = str(os.environ.get("GOOGLE_CLIENT_SECRET"))


# -------------------------------------------------
# ------------- REST_FRAMEWORK SETTINGS -------------------
# -------------------------------------------------
# For customization visit:
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html

# For BlackListing visit:
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    )
}

SIMPLE_JWT = {
    "TOKEN_OBTAIN_SERIALIZER": "accounts.api.serializers.TokenObtainPairSerializer",
    "BLACKLIST_AFTER_ROTATION": True,
    "ROTATE_REFRESH_TOKENS": True,
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=30.0),
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=5.0),
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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
