import os
from pathlib import Path
from app.security import *

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = str(os.environ.get("DJANGO_DEBUG")) == "1"

ALLOWED_HOSTS = ["*"]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ROOT_URLCONF = "app.urls"

ASGI_APPLICATION = "app.asgi.application"

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/login/"
LOGIN_URL_REDIRECT = "/"
LOGOUT_URL = "/logout/"


STATIC_URL: str = "/static/"
STATICFILES_DIRS: list = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        # CompressedManifestStaticFilesStorage -> Yes cache
        # CompressedStaticFilesStorage -> No caching
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "accounts",
    "products",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    # "accounts.middleware.JWTAuthCookieMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
