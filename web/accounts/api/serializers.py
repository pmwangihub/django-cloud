from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer as DefaultTokenRefreshSerializer,
    TokenObtainPairSerializer as DefaultTokenObtainPairSerializer,
)
from rest_framework.exceptions import AuthenticationFailed
from accounts.models import EmailActivation, GuestEmail

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})
    full_name = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = User
        # Notice these fields in exception of password will be returned in response object
        fields = ("email", "full_name", "password1", "password2")

    def validate(self, data):
        # Check that both passwords match
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def validate_email(self, value):
        # Ensure the email is unique
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password1")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        self.send_activation_email(user)
        return user

    def send_activation_email(self, user):
        """
        Sends an activation email to the user with an activation link.
        """
        try:
            obj = EmailActivation.objects.create(user=user, email=user.email)
            request = self.context.get("request")
            obj.send_activation(request=request, origin="react")
        except Exception as e:
            print(e)
            pass


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer class for representing user details.
    This class inherits from Django REST framework's ModelSerializer
    and is used to serialize and deserialize user-related data for the User model.

    Args:
        serializers (serializers.ModelSerializer): Inherits from the base ModelSerializer class.

    Returns:
       UserDetailsSerializer: Serialized representation of the User model with specified fields.
    """

    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "initials",
            "is_active",
            "timestamp",
        )


class TokenObtainPairSerializer(DefaultTokenObtainPairSerializer):
    """
    Custom serializer for obtaining a pair of access and refresh tokens with additional user details.
    This serializer overrides the default TokenObtainPairSerializer to include custom data in the token,
    such as user details, while still following the JWT token generation process.

    Args:
        TokenObtainPairSerializer (TokenObtainPairSerializer): Inherits from the base TokenObtainPairSerializer class.

    Returns:
        MyTokenObtainPairSerializer: A serializer that returns a customized JWT token containing additional user data.

    Methods:
        get_token(user): Generates a token for the given user and adds serialized user details to the token payload.
    """

    @classmethod
    def get_token(cls, user):
        """
        Generates and customizes a JWT token by including user details.

        Args:
            user (User): The user instance for which the token is generated.

        Returns:
            token (dict): The JWT token containing the default payload along with custom user data.
        """
        token = super().get_token(user)
        user = UserDetailsSerializer(instance=user)
        token["user"] = user.data

        return token


class TokenRefreshSerializer(DefaultTokenRefreshSerializer):

    def validate(self, attrs):
        request = self.context["request"]
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            raise AuthenticationFailed(
                "No refresh token found in cookies", code="no_refresh_token"
            )
        attrs["refresh"] = refresh_token
        return super().validate(attrs)
