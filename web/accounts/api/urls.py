from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from accounts.api.views import (
    LoginAPIView,
    LogoutAPIView,
    RefreshTokenAPIView,
    RegisterCreateAPIView,
    UpdateUserProfileAPIView,
    DeleteAccountAPIView,
    AccountEmailActivateAPIView,
    LoginWithGoogleAPIView,
    GoogleCompleteAPIView,
    UserSecuredInfoAPIView,
)


urlpatterns = [
    path("login-google/", LoginWithGoogleAPIView.as_view()),
    path("google-complete/", GoogleCompleteAPIView.as_view()),
    path("logout/", LogoutAPIView.as_view()),
    path("register/", RegisterCreateAPIView.as_view()),
    path("activate/<key>/", AccountEmailActivateAPIView.as_view()),
    path("update-user/", UpdateUserProfileAPIView.as_view()),
    path("delete-account/", DeleteAccountAPIView.as_view()),
    path("user-secured-info/", UserSecuredInfoAPIView.as_view()),
    path(
        "token/",
        include(
            [
                path("", LoginAPIView.as_view()),
                path("refresh/", RefreshTokenAPIView.as_view()),
                path("verify/", TokenVerifyView.as_view()),
            ]
        ),
    ),
]
