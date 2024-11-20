from urllib.parse import urlencode
from django.contrib.auth import login, get_user_model
import requests
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.views import View
from django.views.generic import CreateView, FormView
from django.shortcuts import redirect, render
from app.mixins import NextUrlMixin, RequestFormAttachMixin
from accounts.forms import LoginForm, RegisterForm, GuestForm
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.utils.safestring import mark_safe
from rest_framework_simplejwt.tokens import RefreshToken
from app.utils import random_string_generator
from accounts.models import EmailActivation

User = get_user_model()


class GoogleCallbackView(View):

    def get(self, request, *args, **kwargs):
        code = request.GET.get("code")
        state2 = request.GET.get("state")
        print("State from google: ", state2, "\n")
        state = request.GET.get("state", "template")
        redirect_uri = request.build_absolute_uri("/accounts/google/login/callback/")
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_info_response = requests.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_info_response.json()

        email = user_info.get("email")
        first_name = user_info.get("given_name")
        last_name = user_info.get("family_name")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": f"{first_name} {last_name}",
                "is_active": True,
            },
        )
        EmailActivation.objects.create(user=user, email=email, activated=True)
        login(request, user)

        if state == "react":
            return self.api_redirect(user)

        return redirect("/")

    def api_redirect(self, user):
        token_obj = RefreshToken.for_user(user)
        access = str(token_obj.access_token)
        refresh = str(token_obj)
        response = HttpResponse(status=302)
        params = {"access": access, "refresh": refresh}
        redirect_url = f"{settings.X_ORIGIN_HOST}/auth/complete-google/"
        redirect_url_with_params = f"{redirect_url}?{urlencode(params)}"

        response["Location"] = redirect_url_with_params
        max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=max_age,
        )

        return response


class GoogleLoginView(View):
    def get(self, request, *args, **kwargs):
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = request.build_absolute_uri("/accounts/google/login/callback/")
        scope = "openid email profile"
        state = random_string_generator()
        response_type = "code"
        oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "state": state,
        }
        login_url = f"{oauth_url}?{urlencode(params)}"
        print(login_url)
        return redirect(login_url)


class AlreadyAuthenticatedView(View):
    def get(self, request, *args, **kwargs):
        context = {"page_title": "You are already authenticated"}

        return render(request, "accounts/already_authenticated.html", context)

    @method_decorator(
        ratelimit(key="user_or_ip", rate="3/h", method="POST", block=True)
    )
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class LoginView(NextUrlMixin, RequestFormAttachMixin, FormView):
    """
    View to handle user login using the LoginForm.
    """

    form_class = LoginForm
    success_url = reverse_lazy("home")
    template_name = "accounts/login.html"
    default_next = "/"

    @method_decorator(
        ratelimit(key="user_or_ip", rate="3/h", method="POST", block=True)
    )
    def dispatch(self, request, *args, **kwargs):
        """
        Overrides the dispatch method to apply rate limiting.
        If an IP exceeds 3 attempts per minute, it will be blocked.
        """

        if request.user.is_authenticated:
            return redirect(reverse_lazy("account:already_authenticated"))

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: LoginForm) -> HttpResponse:
        """
        Handle valid login form. Logs the user in and redirects to the next page.
        """
        next_url = self.get_next_url()
        return redirect(next_url)

    def form_invalid(self, form: LoginForm) -> HttpResponse:
        """
        Handle invalid login form submission.
        """
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        """
        Override the get_context_data method to add custom context to the template.
        :param kwargs: Additional keyword arguments.
        :return: Context dictionary with additional data.
        """
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Login to Your Account"
        info_message = """
        <p class="lead">Enter your username & password to login.</p>
        <p class="text-primary">Try to login three times to experiment <code>bruteforce</code> attack </p>
        <p class="text-warning small">NB: the action of retrying to login will block your subsequent 
        request until one hour has elapsed </p>
        """
        context["info_message"] = mark_safe(info_message)
        return context


class GuestRegisterView(NextUrlMixin, RequestFormAttachMixin, CreateView):
    form_class = GuestForm
    default_next = "/register/"

    def get_success_url(self):
        return self.get_next_url()

    def form_invalid(self, form):
        return redirect(self.default_next)


class RegisterView(CreateView):
    """
    View to handle user registration using the RegisterForm.
    """

    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("account:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy("account:already_authenticated"))

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Override to pass the request object to the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_invalid(self, form):
        """
        If the form is invalid, render the form with error messages.
        """

        messages.error(
            self.request,
            "There was an error with your registration. Please check the form.",
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        """
        If the form is valid, save the user and display a success message.
        """

        response = super().form_valid(form)

        messages.success(
            self.request,
            "Your account has been successfully created. Check your email and verify your account.",
        )

        return response

    def get_context_data(self, **kwargs):
        """
        Override the get_context_data method to add custom context to the template.
        :param kwargs: Additional keyword arguments.
        :return: Context dictionary with additional data.
        """
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create an Account"
        context["info_message"] = "Please fill in the form to create an account."
        return context
