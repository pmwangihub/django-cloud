from django.urls import path


from accounts.profile.views import (
    LogoutConfirmView,
    AccountDashboardView,
    AccountEmailActivateView as Activate,
    UserDetailUpdateView as Update,
)


urlpatterns = [
    path("logout-confirm/", LogoutConfirmView.as_view(), name="logout_confirm"),
    path("dashboard/", AccountDashboardView.as_view(), name="dashboard"),
    path("user-settings/", Update.as_view(), name="user_update"),
    path(
        "profile-info/",
        AccountDashboardView.as_view(template_name="profile/profile_info.html"),
        name="profile_info",
    ),
    path(
        "email/confirm/<str:key>/",
        Activate.as_view(),
        name="email_confirm",
    ),
    path(
        "email/resend-activation/", Activate.as_view(), name="email_resend_activation"
    ),
]
