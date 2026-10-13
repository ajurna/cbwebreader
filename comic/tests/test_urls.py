"""Tests for URL resolution that depends on settings."""

import pytest
from django.test import Client


@pytest.mark.parametrize('url', ['/swagger.json', '/swagger.yaml', '/swagger/', '/redoc/'])
def test_schema_urls_resolve(client: Client, url: str) -> None:
    """The schema URLs must match the renderer formats, which no longer include a dot.

    cbreader/urls.py captures the format after the dot because
    SWAGGER_USE_COMPAT_RENDERERS is False.
    """
    assert client.get(url).status_code == 200
