from django.urls import path, include


from accounts.views import (
    LoginView,
    RegisterView,
    AlreadyAuthenticatedView as Already,
)

app_name = "account"


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("already-authenticated/", Already.as_view(), name="already_authenticated"),
    path("profile/", include("accounts.profile.urls")),
    path("passwords/", include("accounts.passwords.urls")),
]
