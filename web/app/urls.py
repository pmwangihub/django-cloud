from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from django.urls import path, include
from app.views import home, home_custom
from accounts.views import GoogleLoginView, GoogleCallbackView


google_callback: str = "accounts/google/login/callback/"
google_login: str = "accounts/google/login/"

urlpatterns = [
    path("", home_custom, name="home"),
    path(google_login, GoogleLoginView.as_view(), name="google_login"),
    path(google_callback, GoogleCallbackView.as_view(), name="google_callback"),
    path("admin/", admin.site.urls),
    path("oAuth/", include("accounts.urls")),
    # API endpoints
    path(
        "api/",
        include(
            [
                path("accounts/", include("accounts.api.urls")),
                path("products/", include("products.api.urls")),
            ]
        ),
    ),
]


if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns = urlpatterns + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
