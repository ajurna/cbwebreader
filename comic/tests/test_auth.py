"""Tests for cookie based JWT authentication."""

import json
from datetime import timedelta

import pytest
from django.conf import settings
from django.test import Client

from cbreader.settings.base import lifetime_from_env
from comic import auth

CREDENTIALS = {'username': 'reader', 'password': 'password12345'}


def _store_cookies(client: Client, response) -> None:
    """Copy Set-Cookie headers into the test client, which does not do it itself."""
    for name, morsel in response.cookies.items():
        if morsel.value:
            client.cookies[name] = morsel.value
        elif name in client.cookies:
            del client.cookies[name]


@pytest.mark.django_db
def test_login_sets_http_only_cookies(client: Client, reader_user) -> None:
    response = client.post('/api/token/', CREDENTIALS)
    assert response.status_code == 200
    # The tokens are not returned to JavaScript, only stored as cookies.
    assert json.loads(response.content) == {}
    for name in (auth.access_cookie_name(), auth.refresh_cookie_name()):
        assert response.cookies[name].value
        assert response.cookies[name]['httponly']


@pytest.mark.django_db
def test_a_cookie_authenticates_a_request(client: Client, reader_user) -> None:
    _store_cookies(client, client.post('/api/token/', CREDENTIALS))
    response = client.get('/api/account/')
    assert response.status_code == 200
    assert json.loads(response.content)['username'] == reader_user.username


@pytest.mark.django_db
def test_anonymous_request_without_a_cookie_is_rejected(client: Client) -> None:
    assert client.get('/api/account/').status_code == 401


@pytest.mark.django_db
def test_the_authorization_header_still_works(client: Client, reader_user) -> None:
    response = client.post('/api/token/', CREDENTIALS)
    token = response.cookies[auth.access_cookie_name()].value
    response = client.get('/api/account/', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200


@pytest.mark.django_db
def test_refresh_rotates_the_access_cookie(client: Client, reader_user) -> None:
    _store_cookies(client, client.post('/api/token/', CREDENTIALS))
    old_access = client.cookies[auth.access_cookie_name()].value
    old_refresh = client.cookies[auth.refresh_cookie_name()].value

    response = client.post('/api/token/refresh/', {})
    assert response.status_code == 200
    _store_cookies(client, response)
    assert client.cookies[auth.access_cookie_name()].value != old_access
    assert client.cookies[auth.refresh_cookie_name()].value != old_refresh

    # The rotated refresh token is blacklisted, so the original one no longer works.
    assert client.post('/api/token/refresh/', {'refresh': old_refresh}).status_code == 401


@pytest.mark.django_db
def test_blacklisting_clears_the_cookies(client: Client, reader_user) -> None:
    _store_cookies(client, client.post('/api/token/', CREDENTIALS))
    response = client.post('/api/token/blacklist/', {})
    assert response.status_code == 204
    _store_cookies(client, response)

    for name in (auth.access_cookie_name(), auth.refresh_cookie_name()):
        assert name not in client.cookies

    assert client.get('/api/account/').status_code == 401


@pytest.mark.django_db
def test_page_images_can_be_loaded_with_a_cookie(client: Client, book, reader_user) -> None:
    """Browser initiated requests cannot send a header, so they rely on the cookie."""
    _store_cookies(client, client.post('/api/token/', CREDENTIALS))
    assert client.get(f'/api/read/{book.selector}/image/1/').status_code == 200


def test_the_session_window_defaults_to_a_month() -> None:
    """A reader away for a month is still reading the same session."""
    assert settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] == timedelta(days=30)
    assert settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] == timedelta(minutes=10)


def test_an_unusable_window_setting_falls_back_to_the_default(monkeypatch) -> None:
    monkeypatch.setenv('JWT_REFRESH_DAYS', 'thirty days')

    assert lifetime_from_env('JWT_REFRESH_DAYS', 'days', 30) == timedelta(days=30)
