from datetime import timedelta
from django.conf import settings
from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.http import HttpResponseServerError
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils import timezone


DEFAULT_ACTIVATION_DAYS = getattr(settings, "DEFAULT_ACTIVATION_DAYS", 7)


class UserManager(BaseUserManager):
    """
    Manager class for custom User model. Handles creation of users,
    staff users, and superusers.
    """

    def create_user(
        self,
        email,
        full_name=None,
        password=None,
        is_active=True,
        is_staff=False,
        is_admin=False,
    ):
        """
        Creates and saves a regular user with the given email and password.

        Args:
            email (str): User's email address.
            full_name (str, optional): User's full name. Defaults to None.
            password (str): User's password.
            is_active (bool, optional): User's activation status. Defaults to True.
            is_staff (bool, optional): Determines if user is a staff member. Defaults to False.
            is_admin (bool, optional): Determines if user is an admin. Defaults to False.

        Raises:
            ValueError: If email or password is not provided.

        Returns:
            user_obj: The created user object.
        """
        if not email:
            raise ValueError("Users must have an email address")
        if not password:
            raise ValueError("Users must have a password")
        user_obj = self.model(email=self.normalize_email(email), full_name=full_name)
        user_obj.set_password(password)  # Set the user's password
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.is_active = is_active
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self, email, full_name=None, password=None):
        """
        Creates and saves a staff user with the given email and password.

        Args:
            email (str): User's email address.
            full_name (str, optional): User's full name. Defaults to None.
            password (str): User's password.

        Returns:
            user: The created staff user.
        """
        user = self.create_user(
            email, full_name=full_name, password=password, is_staff=True
        )
        return user

    def create_superuser(self, email, full_name=None, password=None):
        """
        Creates and saves a superuser with the given email and password.

        Args:
            email (str): User's email address.
            full_name (str, optional): User's full name. Defaults to None.
            password (str): User's password.

        Returns:
            user: The created superuser.
        """
        user = self.create_user(
            email, full_name=full_name, password=password, is_staff=True, is_admin=True
        )
        return user


class User(AbstractBaseUser):
    """
    Custom User model that uses email as the unique identifier.
    Includes fields for full name, admin status, staff status,
    and timestamps for creation.
    """

    email = models.EmailField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    initials = models.CharField(max_length=5, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        """
        Returns the string representation of the user, which is the email.
        """
        return self.email

    @property
    def get_initials(self):
        """
        Returns the initials of the first two letters of the user's email,
        separated by commas.
        """
        if self.email and not self.initials:
            initials = [char for char in self.email[:2].upper()]
            initial = ".".join(initials)
            self.initials = initial
            self.save()

        return self.initials

    def get_full_name(self):
        """
        Returns the full name of the user if available, else returns the email.
        """
        if self.full_name:
            return self.full_name
        return self.email

    def get_short_name(self):
        """
        Returns the email as the short name.
        """
        return self.email

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission.
        Always returns True as this implementation does not check individual permissions.
        """
        return True

    def has_module_perms(self, app_label):
        """
        Returns True if the user has permissions to view the app 'app_label'.
        """
        return True

    @property
    def is_staff(self):
        """
        Returns True if the user is either a staff member or an admin.
        """
        if self.is_admin:
            return True
        return self.staff

    @property
    def is_admin(self):
        """
        Returns True if the user is an admin.
        """
        return self.admin


class EmailActivationQuerySet(models.query.QuerySet):
    """
    Custom QuerySet for filtering email activation objects.
    """

    def confirmable(self):
        """
        Filters and returns EmailActivation objects that are within the
        activation window and have not been activated or force-expired.
        """
        now = timezone.now()
        start_range = now - timedelta(days=DEFAULT_ACTIVATION_DAYS)
        end_range = now
        return self.filter(activated=False, forced_expired=False).filter(
            timestamp__gt=start_range, timestamp__lte=end_range
        )


class EmailActivationManager(models.Manager):
    """
    Manager class for EmailActivation model. Handles querying of activation objects.
    """

    def get_queryset(self):
        """
        Returns the custom QuerySet for EmailActivation.
        """
        return EmailActivationQuerySet(self.model, using=self._db)

    def confirmable(self):
        """
        Returns EmailActivation objects that can still be activated.
        """
        return self.get_queryset().confirmable()

    def email_exists(self, email):
        """
        Checks if an EmailActivation object exists for the given email address
        and is not yet activated.
        """
        return (
            self.get_queryset()
            .filter(Q(email=email) | Q(user__email=email))
            .filter(activated=False)
        )


class EmailActivation(models.Model):
    """
    Model representing an email activation token for user account activation.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    key = models.CharField(max_length=120, blank=True, null=True)
    activated = models.BooleanField(default=False)
    forced_expired = models.BooleanField(default=False)
    expires = models.IntegerField(default=7)
    timestamp = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)

    objects = EmailActivationManager()

    def __str__(self):
        """
        Returns the string representation of the object, which is the email.
        """
        return self.email

    def can_activate(self):
        """
        Checks if the activation can be processed for the current object.
        Uses the custom QuerySet's confirmable method.
        """
        qs = EmailActivation.objects.filter(pk=self.pk).confirmable()
        if qs.exists():
            return True
        return False

    def activate(self):
        """
        Activates the user's account if the activation conditions are met.
        """
        if self.can_activate():
            user = self.user
            user.is_active = True
            user.save()
            self.activated = True
            self.save()
            return True
        return False

    def regenerate(self):
        """
        Resets the activation key for the object.
        """
        self.key = None
        self.save()
        if self.key is not None:
            return True
        return False

    def send_activation(self, request=None, origin="django"):
        """
        Sends an email to the user with a link to activate their account.
        The email includes an activation URL.
        """
        if not request:
            # Which I highly doubt
            return HttpResponseServerError("Intentional 500 error for testing.")

        if not self.activated and not self.forced_expired:
            if self.key:
                if origin == "react":
                    host_path = settings.X_ORIGIN_HOST  # Base URL for React app
                else:
                    host_path = request.build_absolute_uri("/")

                host_name = "Django App" if origin == "django" else "React App"

                if origin == "react":
                    key_path = (
                        f"{settings.X_ORIGIN_ACTIVATE_ACCOUNT_PATH}?key={self.key}"
                    )
                    activation_url = f"{host_path}{key_path}"
                else:
                    key_path = reverse(
                        "account:email_confirm", kwargs={"key": self.key}
                    )
                    activation_url = request.build_absolute_uri(key_path)

                context = {
                    "path": activation_url,
                    "email": self.email,
                    "host_path": host_path,
                    "host_name": host_name,
                }
                message = get_template("emails/accounts/verify.txt").render(context)
                html_ = get_template("emails/accounts/verify.html").render(context)

                subject = "One Click Email Verification"
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [self.email]
                sent_mail = send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    html_message=html_,
                    fail_silently=False,
                )
                return sent_mail
        return False


class GuestEmail(models.Model):
    email = models.EmailField()
    active = models.BooleanField(default=True)
    update = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
