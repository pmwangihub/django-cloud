import requests
import urllib.parse

from yaml import serialize
from app.utils import random_string_generator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import EmailActivation
from accounts.api.serializers import (
    RegisterSerializer,
    UserDetailsSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


User = get_user_model()


class RefreshTokenAPIView(TokenRefreshView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = TokenRefreshSerializer  # Default serializer used by Simple JWT

    def post(self, request, *args, **kwargs):
        data = request.data
        data["refresh"] = request.COOKIES.get("refresh_token")
        serializer = self.get_serializer(data=data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as auth_error:
            response = Response(
                {"detail": f"Authentication failed: {str(auth_error)}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response.delete_cookie("refresh_token")
            return response

        data = serializer.validated_data
        access_token = data["access"]
        response = Response({"access": access_token}, status=status.HTTP_200_OK)

        if bool(settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"]):
            new_refresh_token = data["refresh"]
            max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_token,
                httponly=True,
                secure=settings.DEBUG,
                samesite="Lax",
                max_age=max_age,
            )

        return response


class LoginAPIView(TokenObtainPairView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            refresh_token = response.data["refresh"]
            response.data.pop("refresh", None)

            refresh_token_lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
            max_age = int(refresh_token_lifetime.total_seconds())

            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=settings.DEBUG,
                max_age=max_age,
            )
        return response


class UserSecuredInfoAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, *args, **kwargs):
        serializer = UserDetailsSerializer(request.user)
        return Response(
            {
                "userData": {"user": serializer.data},
                "access_token": "hidden",
                "refresh_token": "hidden",
            },
            status=status.HTTP_200_OK,
        )


class GoogleCompleteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                tokens = RefreshToken(refresh_token)
                new_access_token = str(tokens.access_token)
                new_refresh_token = str(tokens)
                user_token = AccessToken(new_access_token)
                user = User.objects.get(id=user_token["user_id"])
                serializer = UserDetailsSerializer(user)
                response = Response(
                    {
                        "user": serializer.data,
                        "access": new_access_token,
                    },
                    status=status.HTTP_200_OK,
                )
                max_age = int(
                    settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
                )
                response.set_cookie(
                    key="refresh_token",
                    value=new_refresh_token,
                    httponly=True,
                    secure=settings.DEBUG,
                    samesite="Lax",
                    max_age=max_age,
                )
                return response

            except User.DoesNotExist:
                response = Response(
                    {"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                response = Response(
                    {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
                )

        response = Response(
            {"detail": "No refresh token found"}, status=status.HTTP_400_BAD_REQUEST
        )

        response.delete_cookie("refresh_token")
        return response


class LoginWithGoogleAPIView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def get(self, request, *args, **kwargs):
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = request.build_absolute_uri("/accounts/google/login/callback/")
        scope = "openid email profile"
        # state = random_string_generator()
        state = request.query_params.get("client") or "template"
        response_type = "code"
        oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "state": state,
        }
        google_url = f"{oauth_url}?{urllib.parse.urlencode(params)}"
        return Response({"google_url": google_url}, status=status.HTTP_200_OK)


class RegisterCreateAPIView(generics.CreateAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = RegisterSerializer
    queryset = User.objects.all()

    def perform_create(self, serializer):
        """
        Optionally override the `perform_create` method to add extra actions like sending an email
        """
        user = serializer.save()

    def get_serializer_context(self):
        """
        Pass the request to the serializer context
        """
        context = super().get_serializer_context()
        origin = self.request.headers.get("X-Origin", "django")
        context["origin"] = origin
        context["request"] = self.request
        return context


class AccountEmailActivateAPIView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def get(self, request, key, format=None):
        print(key)
        self.key = key
        if key is not None:
            qs = EmailActivation.objects.filter(key__iexact=key)
            confirm_qs = qs.confirmable()
            if confirm_qs.count() == 1:
                obj = confirm_qs.first()
                obj.activate()
                return Response(
                    {"activation": "Your email has been confirmed. Please login."},
                    status=status.HTTP_200_OK,
                )
            else:
                activated_qs = qs.filter(activated=True)
                if activated_qs.exists():
                    return Response(
                        {"activation": "Your email has already been confirmed"},
                        status=status.HTTP_200_OK,
                    )
        return Response(
            {"error": "Activation link failed. Try resending activation link again"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        try:
            refresh = request.COOKIES.get("refresh_token")

            if not refresh:
                response = Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            token = RefreshToken(refresh)
            token.blacklist()
            response = Response(
                {"message": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            response = Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        response.delete_cookie("refresh_token")
        return response


class UpdateUserProfileAPIView(APIView):
    """
    API View for updating user profile information (full_name and initials).
    Only authenticated users can access this endpoint.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def put(self, request, *args, **kwargs):
        user = request.user
        full_name = request.data.get("full_name", user.full_name)
        initials = request.data.get("initials", user.initials)
        user.full_name = full_name
        user.initials = initials
        user.save()
        serializer = UserDetailsSerializer(user)
        return Response({"user": serializer.data}, status=status.HTTP_200_OK)


class DeleteAccountAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            user.delete()
            return Response(
                {"message": "Successfully deleted account."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
