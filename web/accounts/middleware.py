from rest_framework_simplejwt.tokens import RefreshToken


class JWTAuthCookieMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get("access")
        refresh_token = request.COOKIES.get("refresh")

        print(access_token)
        print(refresh_token)

        return self.get_response(request)
