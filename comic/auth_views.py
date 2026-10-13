"""Token views that store JWTs in HttpOnly cookies (see comic/auth.py)."""

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from comic.auth import clear_auth_cookies, refresh_cookie_name, set_auth_cookies


def _refresh_value(request: Request) -> str | None:
    """The refresh token from the request body, or from the refresh cookie."""
    value = request.data.get('refresh') if isinstance(request.data, dict) else None
    return value or request.COOKIES.get(refresh_cookie_name())


class CookieTokenObtainPairView(TokenObtainPairView):
    """Log in: issue tokens and store them in HttpOnly cookies."""

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK and isinstance(response.data, dict):
            set_auth_cookies(response, response.data)
            # The tokens live in HttpOnly cookies, so they are not returned to JavaScript.
            response.data = {}
        return response


class CookieTokenRefreshView(TokenObtainPairView):
    """Refresh using the refresh cookie and update both cookies."""

    serializer_class = TokenRefreshSerializer

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        refresh = _refresh_value(request)
        if not refresh:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'errors': 'No refresh token.'})

        serializer = self.get_serializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise AuthenticationFailed(exc.args[0]) from exc

        response = Response(status=status.HTTP_200_OK)
        set_auth_cookies(response, serializer.validated_data)
        # Keep the cookies out of the body so JavaScript never sees the tokens.
        return response


class CookieTokenBlacklistView(TokenObtainPairView):
    """Log out: blacklist the refresh cookie and clear both cookies."""

    serializer_class = TokenBlacklistSerializer

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        refresh = _refresh_value(request)
        if not refresh:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'errors': 'No refresh token.'})

        serializer = self.get_serializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise AuthenticationFailed(exc.args[0]) from exc

        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response
