from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.views.generic import DetailView, View, UpdateView
from django.views.generic.edit import FormMixin
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.urls import reverse_lazy
from accounts.forms import ReactivateEmailForm, UserDetailChangeForm, LogoutConfirmForm
from accounts.models import EmailActivation
from django.views.generic import FormView
from django.contrib.auth import logout
from app.mixins import NextUrlMixin


class AccountDashboardView(LoginRequiredMixin, DetailView):
    template_name = "profile/dashboard.html"

    def get_object(self):
        return self.request.user


class LogoutConfirmView(NextUrlMixin, LoginRequiredMixin, FormView):
    """
    View to confirm the user's logout.
    """

    form_class = LogoutConfirmForm
    template_name = "accounts/logout_confirm.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["page_title"] = "Confirm Logout"
        context["info_message"] = "Click below to logout"
        return context

    def get_initial(self):
        """
        Populate the next_url hidden field with the home URL by default.
        """
        initial = super().get_initial()
        initial["next_url"] = self.get_next_url()
        return initial

    def form_valid(self, form):
        """
        Handle valid form: log out the user and redirect to the next URL.
        """
        logout(self.request)
        next_url = form.cleaned_data.get("next_url")
        return redirect(next_url)


class AccountEmailActivateView(FormMixin, View):
    success_url = "/oAuth/login/"
    form_class = ReactivateEmailForm
    key = None

    def get(self, request, key=None, *args, **kwargs):
        self.key = key
        if key is not None:
            qs = EmailActivation.objects.filter(key__iexact=key)
            confirm_qs = qs.confirmable()
            if confirm_qs.count() == 1:
                obj = confirm_qs.first()
                obj.activate()
                messages.success(
                    request, "Your email has been confirmed. Please login."
                )
                return redirect("account:login")
            else:
                activated_qs = qs.filter(activated=True)
                if activated_qs.exists():
                    reset_link = reverse("account:password_reset")
                    msg = f"""Your email has already been confirmed
                    Do you need to <a href="{reset_link}">reset your password</a>?
                    """
                    messages.success(request, mark_safe(msg))
                    return redirect("account:login")
        context = {"form": self.get_form(), "key": key}
        return render(request, "accounts/activation-error.html", context)

    def post(self, request, *args, **kwargs):
        print(reverse("account:login"))
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        msg = """Activation link sent, please check your email."""
        request = self.request
        messages.success(request, msg)
        email = form.cleaned_data.get("email")
        obj = EmailActivation.objects.email_exists(email).first()
        user = obj.user
        new_activation = EmailActivation.objects.create(user=user, email=email)
        new_activation.send_activation(request=self.request)
        return super(AccountEmailActivateView, self).form_valid(form)

    def form_invalid(self, form):
        context = {"form": form, "key": self.key}
        return render(self.request, "accounts/activation-error.html", context)


class UserDetailUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserDetailChangeForm
    template_name = "profile/detail-update-view.html"

    def get_object(self):
        return self.request.user

    def get_context_data(self, *args, **kwargs):
        context = super(UserDetailUpdateView, self).get_context_data(*args, **kwargs)
        context["title"] = "Change Your Account Details"
        return context

    def get_success_url(self):
        return reverse("account:profile_info")
