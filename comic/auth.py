"""Cookie based JWT authentication.

Tokens are kept in HttpOnly cookies rather than in JavaScript storage. That is
what makes browser initiated requests work: an `<img>` tag cannot send an
`Authorization` header, so protected page images can only be served through
cookie authentication.

The views live in comic/auth_views.py: importing rest_framework.views here would
resolve DEFAULT_AUTHENTICATION_CLASSES while this module is still being imported.
"""

from typing import Any

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES, JWTAuthentication


def access_cookie_name() -> str:
    return settings.JWT_ACCESS_COOKIE_NAME


def refresh_cookie_name() -> str:
    return settings.JWT_REFRESH_COOKIE_NAME


def _cookie_options() -> dict[str, Any]:
    return {
        'httponly': True,
        'secure': settings.JWT_COOKIE_SECURE,
        'samesite': settings.JWT_COOKIE_SAMESITE,
        'path': settings.JWT_COOKIE_PATH,
    }


def set_auth_cookies(response: Response, tokens: dict[str, Any]) -> None:
    """Write the access and refresh tokens into HttpOnly cookies."""
    simple_jwt = settings.SIMPLE_JWT
    for name, token, lifetime in (
        (access_cookie_name(), tokens.get('access'), simple_jwt['ACCESS_TOKEN_LIFETIME']),
        (refresh_cookie_name(), tokens.get('refresh'), simple_jwt['REFRESH_TOKEN_LIFETIME']),
    ):
        if token:
            response.set_cookie(name, token, max_age=int(lifetime.total_seconds()), **_cookie_options())


def clear_auth_cookies(response: Response) -> None:
    for name in (access_cookie_name(), refresh_cookie_name()):
        response.delete_cookie(name, path=settings.JWT_COOKIE_PATH)


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate from the Authorization header, or from the access cookie.

    Keeping the header path means API clients that send a bearer token still work.
    """

    def get_header(self, request: Request) -> bytes | None:
        header = super().get_header(request)
        if header:
            return header
        token = request.COOKIES.get(access_cookie_name())
        if not token:
            return None
        return f'{AUTH_HEADER_TYPES[0]} {token}'.encode()
