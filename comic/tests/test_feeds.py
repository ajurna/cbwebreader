"""Tests for the RSS feed."""

import xml.etree.ElementTree as ElementTree

import pytest

UNKNOWN = '00000000-0000-0000-0000-000000000000'


def get_channel(client, feed_id) -> ElementTree.Element:
    response = client.get(f'/feed/{feed_id}/')
    assert response.status_code == 200
    return ElementTree.fromstring(response.content.decode('utf-8')).find('channel')


@pytest.mark.django_db
def test_feed_lists_books_the_reader_is_allowed_to_read(client, reader_user, book) -> None:
    channel = get_channel(client, reader_user.usermisc.feed_id)
    assert channel.findtext('title') == 'CBWebReader Recent Comics'

    items = channel.findall('item')
    assert [item.findtext('title') for item in items] == ['issue.cbz']
    # Django's syndication framework prefixes the site host to item_link.
    assert items[0].findtext('link').endswith(f'#/read/{book.selector}/')
    assert items[0].findtext('description')


@pytest.mark.django_db
def test_feed_skips_books_above_the_readers_allowance(client, restricted_user, book) -> None:
    assert get_channel(client, restricted_user.usermisc.feed_id).findall('item') == []


@pytest.mark.django_db
def test_unknown_feed_id_returns_404(client) -> None:
    assert client.get(f'/feed/{UNKNOWN}/').status_code == 404
