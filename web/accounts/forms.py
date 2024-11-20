from django import forms
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.urls import reverse
from django.utils.safestring import mark_safe

User = get_user_model()

from accounts.models import EmailActivation, GuestEmail


class LogoutConfirmForm(forms.Form):
    """
    Form to confirm logout with a hidden next_url input.
    """

    next_url = forms.CharField(widget=forms.HiddenInput)


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "id": "email",
                "placeholder": "Email address",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "id": "password1",
                "placeholder": "Password",
            }
        ),
    )

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        request = self.request
        data = self.cleaned_data
        email = data.get("email")
        password = data.get("password")
        qs = User.objects.filter(email=email)
        if qs.exists():

            not_active = qs.filter(is_active=False)
            if not_active.exists():
                ## not active, check email activation
                link = reverse("account:email_resend_activation")
                reconfirm_msg = (
                    f"""Go to <a href='{link}'> resend confirmation email</a>."""
                )
                confirm_email = EmailActivation.objects.filter(email=email)
                is_confirmable = confirm_email.confirmable().exists()
                if is_confirmable:
                    msg1 = (
                        "Please check your email to confirm your account or "
                        + reconfirm_msg
                    )
                    raise forms.ValidationError(mark_safe(msg1))
                email_confirm_exists = EmailActivation.objects.email_exists(
                    email
                ).exists()
                if email_confirm_exists:
                    msg2 = "Email not confirmed. " + reconfirm_msg
                    raise forms.ValidationError(mark_safe(msg2))
                if not is_confirmable and not email_confirm_exists:
                    raise forms.ValidationError("This user is inactive.")

        user = authenticate(request, username=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid credentials")
        login(request, user)
        self.user = user
        return data


class ReactivateEmailForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "id": "email",
                "placeholder": "Email address",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        qs = EmailActivation.objects.email_exists(email)
        if not qs.exists():
            register_link = reverse("account:register")
            msg = f"""This email does not exists, would you like to <a href="{register_link}">register</a>?
            """
            raise forms.ValidationError(mark_safe(msg))
        return email


class UserAdminCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "email",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserDetailChangeForm(forms.ModelForm):
    full_name = forms.CharField(
        label="Name",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    initials = forms.CharField(
        label="Initials",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["full_name", "initials"]


class UserAdminChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("full_name", "email", "password", "is_active", "admin", "initials")

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class GuestForm(forms.ModelForm):
    # email    = forms.EmailField()
    class Meta:
        model = GuestEmail
        fields = ["email"]

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(GuestForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # Save the provided password in hashed format
        obj = super(GuestForm, self).save(commit=False)
        if commit:
            obj.save()
            request = self.request
            request.session["guest_email_id"] = obj.id
        return obj


class RegisterForm(forms.ModelForm):
    """
    A form for creating new users with Bootstrap styling and password confirmation.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(RegisterForm, self).__init__(*args, **kwargs)

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "id": "password1",
                "placeholder": "Enter password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "id": "password2",
                "placeholder": "Confirm password",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "full_name",
            "email",
        )

        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Full name (Optional)"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Email address",
                }
            ),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False
        if commit:
            user.save()
        self.send_activation_email(user)
        return user

    def send_activation_email(self, user):
        """
        Sends an activation email to the user with an activation link.
        """
        try:
            # A lot can go wrong here, all to do with user instance
            obj = EmailActivation.objects.create(user=user, email=user.email)
            obj.send_activation(request=self.request)
        except Exception as e:
            print(e)
            pass
