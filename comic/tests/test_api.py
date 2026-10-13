"""Tests for the API behaviour of the comic viewsets."""

import json

import pytest

from comic import models
from comic.tests.factories import make_cbz

UNKNOWN = '00000000-0000-0000-0000-000000000000'


@pytest.mark.django_db
def test_unknown_directory_returns_404(client, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/browse/{UNKNOWN}/').status_code == 404


@pytest.mark.django_db
def test_unknown_selector_returns_404_in_breadcrumbs(client, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/browse/{UNKNOWN}/breadcrumbs/').status_code == 404


@pytest.mark.django_db
def test_unknown_book_returns_404_for_an_image(client, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/read/{UNKNOWN}/image/1/').status_code == 404


@pytest.mark.django_db
def test_unknown_book_returns_404_for_the_type_action(client, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/read/{UNKNOWN}/type/').status_code == 404


@pytest.mark.django_db
def test_image_requires_authentication(client, book) -> None:
    assert client.get(f'/api/read/{book.selector}/image/1/').status_code == 401


@pytest.mark.django_db
def test_image_is_blocked_for_a_user_below_the_rating(client, book, restricted_user) -> None:
    client.force_login(restricted_user)
    assert client.get(f'/api/read/{book.selector}/image/1/').status_code == 403


@pytest.mark.django_db
def test_image_returns_the_page_for_an_allowed_user(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.get(f'/api/read/{book.selector}/image/1/')
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'
    assert b''.join(response.streaming_content)


@pytest.mark.django_db
def test_read_view_is_blocked_for_a_user_below_the_rating(client, book, restricted_user) -> None:
    client.force_login(restricted_user)
    assert client.get(f'/api/read/{book.selector}/').status_code == 403


@pytest.mark.django_db
def test_read_view_returns_progress_for_an_allowed_user(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.get(f'/api/read/{book.selector}/')
    assert response.status_code == 200
    assert response.json()['pages'] == 3
    assert response.json()['title'] == 'issue.cbz'


@pytest.mark.django_db
def test_set_page_creates_the_status_and_marks_the_book_finished(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.put(
        f'/api/read/{book.selector}/set_page/',
        data={'page': book.page_count - 1},
        content_type='application/json',
    )
    assert response.status_code == 200
    status = models.ComicStatus.objects.get(user=reader_user, comic=book)
    assert status.last_read_page == 2
    assert status.finished
    assert not status.unread


@pytest.mark.django_db
def test_set_page_leaves_the_book_unfinished_before_the_last_page(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.put(
        f'/api/read/{book.selector}/set_page/',
        data={'page': 1},
        content_type='application/json',
    )
    assert response.status_code == 200
    status = models.ComicStatus.objects.get(user=reader_user, comic=book)
    assert not status.finished


@pytest.mark.django_db
def test_mark_read_records_the_last_page(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.put(
        '/api/action/mark_read/',
        data={'selectors': [str(book.selector)]},
        content_type='application/json',
    )
    assert response.status_code == 200
    status = models.ComicStatus.objects.get(user=reader_user, comic=book)
    assert status.last_read_page == book.page_count - 1
    assert status.finished


@pytest.mark.django_db
def test_directory_update_cascades_to_children(client, admin_user) -> None:
    client.force_login(admin_user)
    parent = models.Directory.objects.create(name='Parent', classification=models.Directory.Classification.C_18)
    child = models.Directory.objects.create(name='Child', parent=parent)

    response = client.put(
        f'/api/directory/{parent.selector}/',
        data={'classification': models.Directory.Classification.C_PG},
        content_type='application/json',
    )

    assert response.status_code == 200
    assert sorted(item['classification'] for item in response.json()) == [1, 1]
    child.refresh_from_db()
    assert child.classification == models.Directory.Classification.C_PG


@pytest.mark.django_db
def test_directory_partial_update_does_not_cascade(client, admin_user) -> None:
    client.force_login(admin_user)
    parent = models.Directory.objects.create(name='Parent', classification=models.Directory.Classification.C_18)
    child = models.Directory.objects.create(name='Child', parent=parent)

    response = client.patch(
        f'/api/directory/{child.selector}/',
        data={'classification': models.Directory.Classification.C_15},
        content_type='application/json',
    )

    assert response.status_code == 200
    assert response.json() == {'selector': str(child.selector), 'classification': 3}
    parent.refresh_from_db()
    assert parent.classification == models.Directory.Classification.C_18


@pytest.mark.django_db
def test_directory_partial_update_rejects_an_unknown_classification(client, admin_user) -> None:
    client.force_login(admin_user)
    directory = models.Directory.objects.create(name='Parent')
    response = client.patch(
        f'/api/directory/{directory.selector}/',
        data={'classification': 9},
        content_type='application/json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_browse_listing_does_not_write_to_the_database(client, reader_user, comic_volume) -> None:
    """Listing is read only, so a browse request cannot race with the scan."""
    client.force_login(reader_user)
    target = comic_volume / 'Series'
    target.mkdir()
    make_cbz(target / 'issue.cbz', pages=2)

    assert client.get('/api/browse/').status_code == 200
    assert models.ComicBook.objects.count() == 0
    assert models.ComicStatus.objects.count() == 0


@pytest.mark.django_db
def test_scan_endpoint_indexes_files_that_are_only_on_disk(client, reader_user, comic_volume) -> None:
    client.force_login(reader_user)
    target = comic_volume / 'Series'
    target.mkdir()
    make_cbz(target / 'issue.cbz', pages=2)

    assert [entry['title'] for entry in client.get('/api/browse/').json()] == []

    response = client.post('/api/browse/scan/', data='{}', content_type='application/json')
    assert response.status_code == 200
    assert [entry['title'] for entry in response.json()] == ['Series']

    directory = models.Directory.objects.get(name='Series')
    response = client.post('/api/browse/scan/',
                           data=json.dumps({'selector': str(directory.selector)}),
                           content_type='application/json')
    assert response.status_code == 200
    entries = response.json()
    assert [entry['title'] for entry in entries] == ['issue.cbz']
    assert entries[0]['type'] == 'ComicBook'
    assert entries[0]['total'] == 2
    assert entries[0]['progress'] == 0
    assert entries[0]['unread'] is True


@pytest.mark.django_db
def test_scan_endpoint_requires_authentication(client) -> None:
    assert client.post('/api/browse/scan/', data='{}', content_type='application/json').status_code == 401
