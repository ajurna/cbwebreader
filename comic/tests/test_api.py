"""Tests for the API behaviour of the comic viewsets."""

import json
from datetime import timedelta

import pytest
from django.utils import timezone

from comic import models
from comic.tests.factories import make_cbz, make_pdf

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
    assert response.json()['directory'] == str(book.directory.selector)


@pytest.mark.django_db
def test_read_view_reports_no_folder_for_an_unfiled_book(client, comic_volume, reader_user) -> None:
    # retrieve() opens the archive to check the page count, so the file has to exist.
    make_cbz(comic_volume / 'loose.cbz', pages=1)
    unfiled = models.ComicBook.objects.create(file_name='loose.cbz', page_count=1)
    client.force_login(reader_user)
    assert client.get(f'/api/read/{unfiled.selector}/').json()['directory'] is None


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
    # metadata=False so the titles in this test are the file names, not ComicInfo titles
    make_cbz(target / 'issue.cbz', pages=2, metadata=False)

    assert [entry['title'] for entry in client.get('/api/browse/').json()['results']] == []

    response = client.post('/api/browse/scan/', data='{}', content_type='application/json')
    assert response.status_code == 200
    assert [entry['title'] for entry in response.json()['results']] == ['Series']

    directory = models.Directory.objects.get(name='Series')
    response = client.post('/api/browse/scan/',
                           data=json.dumps({'selector': str(directory.selector)}),
                           content_type='application/json')
    assert response.status_code == 200
    entries = response.json()['results']
    assert [entry['title'] for entry in entries] == ['issue.cbz']
    assert entries[0]['type'] == 'ComicBook'
    assert entries[0]['total'] == 2
    assert entries[0]['progress'] == 0
    assert entries[0]['unread'] is True


@pytest.mark.django_db
def test_browse_search_matches_names_in_both_queries(client, reader_user, comic_volume) -> None:
    client.force_login(reader_user)
    series = comic_volume / 'Transmetropolitan'
    series.mkdir()
    # metadata=False so the titles in this test are the file names, not ComicInfo titles
    make_cbz(series / 'issue 1.cbz', pages=2, metadata=False)
    make_cbz(comic_volume / 'other.cbz', pages=2)

    # A root scan indexes the root only, so the folder has to be scanned as well.
    client.post('/api/browse/scan/', data='{}', content_type='application/json')
    folder = models.Directory.objects.get(name='Transmetropolitan')
    client.post('/api/browse/scan/', data=json.dumps({'selector': str(folder.selector)}),
                content_type='application/json')

    body = client.get('/api/browse/', data={'search': 'trans'}).json()
    assert [entry['title'] for entry in body['results']] == ['Transmetropolitan']

    body = client.get(f'/api/browse/{folder.selector}/', data={'search': 'issue 1'}).json()
    assert [entry['title'] for entry in body['results']] == ['issue 1.cbz']

    assert client.get('/api/browse/', data={'search': 'nothing'}).json()['results'] == []


@pytest.mark.django_db
def test_browse_read_filter_follows_the_finished_flag(client, book, reader_user) -> None:
    client.force_login(reader_user)
    status = models.ComicStatus.objects.create(user=reader_user, comic=book, last_read_page=1)

    body = client.get('/api/browse/', data={'read': 'false'}).json()
    assert [entry['title'] for entry in body['results']] == ['Rated']
    assert client.get('/api/browse/', data={'read': 'true'}).json()['results'] == []

    status.finished = True
    status.save()
    body = client.get('/api/browse/', data={'read': 'true'}).json()
    assert [entry['title'] for entry in body['results']] == ['Rated']
    assert client.get('/api/browse/', data={'read': 'false'}).json()['results'] == []


@pytest.mark.django_db
def test_browse_listing_is_paginated(client, reader_user, comic_volume) -> None:
    client.force_login(reader_user)
    for index in range(12):
        make_cbz(comic_volume / f'book{index:02d}.cbz', pages=1)
    client.post('/api/browse/scan/', data='{}', content_type='application/json')

    body = client.get('/api/browse/').json()
    assert body['count'] == 12
    assert len(body['results']) == 10
    assert body['next']

    assert len(client.get('/api/browse/', data={'page': 2}).json()['results']) == 2
    assert client.get('/api/browse/', data={'page': 3}).status_code == 404
    assert len(client.get('/api/browse/', data={'page_size': 100}).json()['results']) == 12


@pytest.mark.django_db
def test_scan_endpoint_requires_authentication(client) -> None:
    assert client.post('/api/browse/scan/', data='{}', content_type='application/json').status_code == 401


@pytest.mark.django_db
def test_continue_reading_lists_books_that_are_partway_through(client, book, reader_user) -> None:
    client.force_login(reader_user)
    models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1)

    response = client.get('/api/read/continue/')
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]['selector'] == str(book.selector)
    assert entries[0]['progress'] == 1
    assert entries[0]['total'] == 3
    assert entries[0]['directory'] == str(book.directory.selector)


@pytest.mark.django_db
def test_continue_reading_ignores_finished_and_untouched_books(client, reader_user) -> None:
    """A finished book is not listed, but the next issue in the same series is on deck."""
    directory = models.Directory.objects.create(name='Series')
    finished = models.ComicBook.objects.create(file_name='issue 1.cbz', directory=directory, page_count=2)
    next_issue = models.ComicBook.objects.create(file_name='issue 2.cbz', directory=directory, page_count=2)
    models.ComicStatus.objects.create(comic=finished, user=reader_user, last_read_page=2,
                                     finished=True, unread=False)
    models.ComicStatus.objects.create(comic=next_issue, user=reader_user, last_read_page=0)

    client.force_login(reader_user)
    entries = client.get('/api/read/continue/').json()
    assert len(entries) == 1
    assert entries[0]['selector'] == str(next_issue.selector)
    assert entries[0]['on_deck'] is True
    assert entries[0]['progress'] == 0


@pytest.mark.django_db
def test_continue_reading_orders_issues_by_number_not_by_string(client, reader_user) -> None:
    directory = models.Directory.objects.create(name='Series')
    second = models.ComicBook.objects.create(file_name='issue 2.cbz', directory=directory, page_count=2)
    tenth = models.ComicBook.objects.create(file_name='issue 10.cbz', directory=directory, page_count=2)
    models.ComicStatus.objects.create(comic=second, user=reader_user, last_read_page=2,
                                     finished=True, unread=False)

    client.force_login(reader_user)
    assert [entry['title'] for entry in client.get('/api/read/continue/').json()] == [tenth.file_name]


@pytest.mark.django_db
def test_reader_next_issue_follows_issue_number_not_the_string(client, comic_volume, reader_user) -> None:
    """The shelf and the reader must agree about which issue is next."""
    directory = models.Directory.objects.create(name='Series')
    volume = comic_volume / 'Series'
    volume.mkdir(parents=True, exist_ok=True)
    second = models.ComicBook.objects.create(file_name='issue 2.cbz', directory=directory, page_count=2)
    tenth = models.ComicBook.objects.create(file_name='issue 10.cbz', directory=directory, page_count=2)
    make_cbz(volume / 'issue 2.cbz', pages=2)
    make_cbz(volume / 'issue 10.cbz', pages=2)

    client.force_login(reader_user)
    data = client.get(f'/api/read/{second.selector}/').json()
    assert data['next_comic']['selector'] == str(tenth.selector)


@pytest.mark.django_db
def test_continue_reading_lists_one_entry_per_series(client, book, reader_user) -> None:
    """A book that is partway through is already the next thing to read in that series."""
    client.force_login(reader_user)
    models.ComicBook.objects.create(file_name='issue 2.cbz', directory=book.directory, page_count=2)
    models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1, unread=False)
    earlier = models.Directory.objects.create(name='Earlier')
    finished = models.ComicBook.objects.create(file_name='issue 1.cbz', directory=earlier, page_count=2)
    models.ComicStatus.objects.create(comic=finished, user=reader_user, last_read_page=2,
                                     finished=True, unread=False)
    models.ComicBook.objects.create(file_name='issue 2.cbz', directory=earlier, page_count=2)

    entries = client.get('/api/read/continue/').json()
    assert sorted(entry['title'] for entry in entries) == sorted([book.file_name, 'issue 2.cbz'])
    assert sorted(entry['on_deck'] for entry in entries) == [False, True]


@pytest.mark.django_db
def test_continue_reading_skips_older_issues_in_the_same_series(client, reader_user) -> None:
    """The shelf shows what to read next in a series, not every book that was started."""
    directory = models.Directory.objects.create(name='Series')
    older = models.ComicBook.objects.create(file_name='issue 1.cbz', directory=directory, page_count=2)
    current = models.ComicBook.objects.create(file_name='issue 2.cbz', directory=directory, page_count=2)
    next_issue = models.ComicBook.objects.create(file_name='issue 3.cbz', directory=directory, page_count=2)

    client.force_login(reader_user)
    stale = models.ComicStatus.objects.create(comic=older, user=reader_user, last_read_page=1, unread=False)
    models.ComicStatus.objects.create(comic=current, user=reader_user, last_read_page=2,
                                     finished=True, unread=False)

    entries = client.get('/api/read/continue/').json()
    assert [entry['title'] for entry in entries] == [next_issue.file_name]
    assert entries[0]['on_deck'] is True

    # Reading the older issue again makes it the thing to continue.
    models.ComicStatus.objects.filter(pk=stale.pk).update(updated=timezone.now())
    entries = client.get('/api/read/continue/').json()
    assert [entry['title'] for entry in entries] == [older.file_name]
    assert entries[0]['on_deck'] is False


@pytest.mark.django_db
def test_continue_reading_orders_the_shelf_by_most_recently_read(client, reader_user) -> None:
    recent_dir = models.Directory.objects.create(name='Recent')
    older_dir = models.Directory.objects.create(name='Older')
    recent = models.ComicBook.objects.create(file_name='recent.cbz', directory=recent_dir, page_count=5)
    older = models.ComicBook.objects.create(file_name='older.cbz', directory=older_dir, page_count=5)

    client.force_login(reader_user)
    for book, days in ((older, 5), (recent, 1)):
        comic_status = models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1)
        # `updated` is auto_now, so set it after the insert.
        models.ComicStatus.objects.filter(pk=comic_status.pk).update(updated=timezone.now() - timedelta(days=days))

    assert [entry['title'] for entry in client.get('/api/read/continue/').json()] == [recent.file_name, older.file_name]


@pytest.mark.django_db
def test_continue_reading_only_shows_the_logged_in_users_progress(client, book, reader_user) -> None:
    client.force_login(reader_user)
    other_user = models.User.objects.create_user('other', 'other@example.com', 'password12345')
    models.ComicStatus.objects.create(comic=book, user=other_user, last_read_page=1)

    assert client.get('/api/read/continue/').json() == []


@pytest.mark.django_db
def test_continue_reading_includes_books_that_are_read_but_not_finished(client, book, reader_user) -> None:
    """Reading a page sets unread to False, so the panel must not require unread=True."""
    client.force_login(reader_user)
    models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1, unread=False)

    assert len(client.get('/api/read/continue/').json()) == 1


@pytest.mark.django_db
def test_continue_reading_can_be_scoped_to_a_folder(client, book, reader_user) -> None:
    other = models.Directory.objects.create(name='Other')
    other_book = models.ComicBook.objects.create(file_name='other.cbz', directory=other, page_count=5)
    models.ComicStatus.objects.create(comic=other_book, user=reader_user, last_read_page=2)
    models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1)

    client.force_login(reader_user)
    entries = client.get(f'/api/read/continue/?directory={book.directory.selector}').json()
    assert [entry['title'] for entry in entries] == [book.file_name]
    assert client.get(f'/api/read/continue/?directory={UNKNOWN}').status_code == 404


@pytest.mark.django_db
def test_browse_search_matches_metadata_fields(client, reader_user, comic_volume) -> None:
    client.force_login(reader_user)
    series = comic_volume / 'Series'
    series.mkdir()
    make_cbz(series / 'issue.cbz', pages=2)

    # A root scan indexes the root only, so the folder has to be scanned as well.
    client.post('/api/browse/scan/', data='{}', content_type='application/json')
    folder = models.Directory.objects.get(name='Series')
    client.post('/api/browse/scan/', data=json.dumps({'selector': str(folder.selector)}),
                content_type='application/json')

    # The book is inside a folder, so the search has to be run inside that folder.
    for term in ('test title', 'test series'):
        body = client.get(f'/api/browse/{folder.selector}/', data={'search': term}).json()
        assert [entry['title'] for entry in body['results']] == ['The Test Title']


@pytest.mark.django_db
def test_browse_reports_metadata_for_books_and_nothing_for_folders(client, reader_user, book) -> None:
    book.metadata_title = 'The Test Title'
    book.series = 'Test Series'
    book.issue_number = '12'
    book.writer = 'Test Writer'
    book.artist = 'Test Artist'
    book.year = 2003
    book.save()

    client.force_login(reader_user)
    folder = client.get('/api/browse/').json()['results'][0]
    assert folder['type'] == 'Directory'
    assert folder['metadata'] == {}

    entry = client.get(f'/api/browse/{book.directory.selector}/').json()['results'][0]
    assert entry['title'] == 'The Test Title'
    assert entry['metadata'] == {'series': 'Test Series', 'issue': '12', 'writer': 'Test Writer',
                                 'artist': 'Test Artist', 'year': 2003}


@pytest.mark.django_db
def test_image_page_past_the_end_of_the_book_returns_404(client, book, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/read/{book.selector}/image/{book.page_count + 1}/').status_code == 404


@pytest.mark.django_db
def test_image_of_a_file_that_is_not_a_real_pdf_returns_404(client, reader_user, comic_volume) -> None:
    (comic_volume / 'broken.pdf').write_bytes(b'this is not a pdf')
    broken = models.ComicBook.objects.create(file_name='broken.pdf')
    client.force_login(reader_user)
    assert client.get(f'/api/read/{broken.selector}/image/1/').status_code == 404


@pytest.mark.django_db
def test_generate_thumbnail_endpoint_generates_one_for_a_book(client, book, reader_user, media_root) -> None:
    client.force_login(reader_user)
    response = client.get(f'/api/generate_thumbnail/{book.selector}/')
    assert response.status_code == 200
    assert response.json()['thumbnail'].endswith('.jpg')


@pytest.mark.django_db
def test_generate_thumbnail_endpoint_reports_nothing_for_a_corrupt_archive(
        client, reader_user, comic_volume, media_root) -> None:
    (comic_volume / 'broken.cbz').write_bytes(b'this is not an archive')
    broken = models.ComicBook.objects.create(file_name='broken.cbz', page_count=1)
    client.force_login(reader_user)
    response = client.get(f'/api/generate_thumbnail/{broken.selector}/')
    assert response.status_code == 200
    assert response.json()['thumbnail'] is None
    assert list(media_root.glob('*')) == []


@pytest.mark.django_db
def test_generate_thumbnail_endpoint_returns_404_for_an_unknown_selector(client, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/generate_thumbnail/{UNKNOWN}/').status_code == 404


@pytest.mark.django_db
def test_breadcrumbs_for_a_book_run_from_home_to_the_book(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.get(f'/api/browse/{book.selector}/breadcrumbs/')
    assert [item['name'] for item in response.json()] == ['Home', 'Rated', 'issue.cbz']


@pytest.mark.django_db
def test_recent_search_only_matches_file_names(client, book, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get('/api/recent/?search_text=issue').json()['count'] == 1
    assert client.get('/api/recent/?search_text=writer').json()['count'] == 0


@pytest.mark.django_db
def test_history_lists_the_books_the_user_started_reading(client, book, reader_user) -> None:
    client.force_login(reader_user)
    models.ComicStatus.objects.create(comic=book, user=reader_user, unread=False, finished=True)
    other = models.ComicBook.objects.create(file_name='other.cbz')
    models.ComicStatus.objects.create(comic=other, user=reader_user, unread=True, finished=False)
    assert [item['selector'] for item in client.get('/api/history/').json()['results']] == [str(book.selector)]


@pytest.mark.django_db
def test_recent_and_history_block_books_above_the_users_allowance(client, book, restricted_user) -> None:
    client.force_login(restricted_user)
    models.ComicStatus.objects.create(comic=book, user=restricted_user, unread=False, finished=True)
    assert client.get('/api/recent/').json()['count'] == 0
    assert client.get('/api/history/').json()['count'] == 0


@pytest.mark.django_db
def test_mark_read_updates_a_status_that_already_exists(client, book, reader_user) -> None:
    client.force_login(reader_user)
    status = models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1)
    client.put('/api/action/mark_read/', data={'selectors': [str(book.selector)]}, content_type='application/json')
    status.refresh_from_db()
    assert status.last_read_page == book.page_count - 1
    assert not status.unread and status.finished


@pytest.mark.django_db
def test_mark_read_accepts_a_folder_and_marks_the_books_below_it(client, book, reader_user) -> None:
    client.force_login(reader_user)
    parent = models.Directory.objects.create(name='Parent')
    child = models.Directory.objects.create(name='Child', parent=parent)
    models.ComicBook.objects.create(file_name='child.cbz', directory=child)
    client.put('/api/action/mark_read/', data={'selectors': [str(parent.selector)]}, content_type='application/json')
    assert models.ComicStatus.objects.filter(user=reader_user, finished=True).count() == 1


@pytest.mark.django_db
def test_mark_read_rejects_selectors_that_are_not_uuids(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.put('/api/action/mark_read/', data={'selectors': ['not-a-uuid']}, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_mark_read_on_a_book_with_no_pages_stays_on_page_zero(client, reader_user) -> None:
    client.force_login(reader_user)
    book = models.ComicBook.objects.create(file_name='empty.cbz', page_count=0)
    status = models.ComicStatus.objects.create(comic=book, user=reader_user)
    client.put('/api/action/mark_read/', data={'selectors': [str(book.selector)]}, content_type='application/json')
    status.refresh_from_db()
    assert status.last_read_page == 0


@pytest.mark.django_db
def test_mark_unread_resets_a_status_that_already_exists(client, book, reader_user) -> None:
    client.force_login(reader_user)
    status = models.ComicStatus.objects.create(comic=book, user=reader_user, unread=False, finished=True,
                                               last_read_page=2)
    client.put('/api/action/mark_unread/', data={'selectors': [str(book.selector)]}, content_type='application/json')
    status.refresh_from_db()
    assert status.unread and not status.finished and status.last_read_page == 0


@pytest.mark.django_db
def test_mark_unread_creates_a_status_for_a_book_that_has_none(client, book, reader_user) -> None:
    client.force_login(reader_user)
    client.put('/api/action/mark_unread/', data={'selectors': [str(book.selector)]}, content_type='application/json')
    status = models.ComicStatus.objects.get(comic=book, user=reader_user)
    assert status.unread and not status.finished and status.last_read_page == 0


@pytest.mark.django_db
def test_continue_reading_falls_back_to_20_for_an_unreadable_limit(client, book, reader_user) -> None:
    client.force_login(reader_user)
    models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=1)
    assert client.get('/api/read/continue/?limit=abc').status_code == 200


@pytest.mark.django_db
def test_user_classification_update_sets_the_rating(client, admin_user) -> None:
    client.force_login(admin_user)
    response = client.patch(f'/api/users/{admin_user.id}/set_classification/', data={'classification': 2},
                            content_type='application/json')
    assert response.status_code == 200
    assert models.UserMisc.objects.get(user=admin_user).allowed_to_read == 2


@pytest.mark.django_db
def test_user_classification_update_rejects_an_unknown_rating(client, admin_user) -> None:
    client.force_login(admin_user)
    response = client.patch(f'/api/users/{admin_user.id}/set_classification/', data={'classification': 9},
                            content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_password_reset_needs_the_matching_username(client, admin_user, reader_user) -> None:
    client.force_login(admin_user)
    response = client.patch(f'/api/users/{reader_user.id}/reset_password/', data={'username': 'someone-else'},
                            content_type='application/json')
    assert response.status_code == 400
    assert reader_user.check_password('password12345')


@pytest.mark.django_db
def test_admin_password_reset_sets_a_new_password(client, admin_user, reader_user) -> None:
    client.force_login(admin_user)
    response = client.patch(f'/api/users/{reader_user.id}/reset_password/', data={'username': reader_user.username},
                            content_type='application/json')
    assert response.status_code == 200
    reader_user.refresh_from_db()
    assert reader_user.check_password(response.json()['password'])


@pytest.mark.django_db
def test_account_password_reset_changes_the_password(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/reset_password/', data={
        'username': reader_user.username,
        'old_password': 'password12345',
        'new_password': 'a-new-longer-password',
        'new_password_confirm': 'a-new-longer-password',
    }, content_type='application/json')
    assert response.status_code == 200
    reader_user.refresh_from_db()
    assert reader_user.check_password('a-new-longer-password')


@pytest.mark.django_db
def test_account_password_reset_rejects_the_wrong_old_password(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/reset_password/', data={
        'username': reader_user.username,
        'old_password': 'wrong',
        'new_password': 'a-new-longer-password',
        'new_password_confirm': 'a-new-longer-password',
    }, content_type='application/json')
    assert response.status_code == 400
    assert 'Password Incorrect' in response.json()['errors']


@pytest.mark.django_db
def test_account_password_reset_rejects_passwords_that_do_not_match(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/reset_password/', data={
        'username': reader_user.username,
        'old_password': 'password12345',
        'new_password': 'a-new-longer-password',
        'new_password_confirm': 'something-else-long',
    }, content_type='application/json')
    assert response.status_code == 400
    assert response.json()['errors']['non_field_errors'] == ['New passwords do not match']


@pytest.mark.django_db
def test_account_password_reset_rejects_a_weak_password(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/reset_password/', data={
        'username': reader_user.username,
        'old_password': 'password12345',
        'new_password': 'short',
        'new_password_confirm': 'short',
    }, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_account_email_update_needs_the_password(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/update_email/', data={
        'username': reader_user.username,
        'email': 'new@example.com',
        'password': 'wrong',
    }, content_type='application/json')
    assert response.status_code == 400
    assert reader_user.email == 'reader@example.com'


@pytest.mark.django_db
def test_account_email_update_changes_the_email(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/update_email/', data={
        'username': reader_user.username,
        'email': 'new@example.com',
        'password': 'password12345',
    }, content_type='application/json')
    assert response.status_code == 200
    assert response.json()['email'] == 'new@example.com'


@pytest.mark.django_db
def test_feed_id_returns_404_for_a_user_with_no_misc_row(client, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get('/api/account/feed_id/').status_code == 404


@pytest.mark.django_db
def test_feed_id_returns_the_users_feed_id(client, restricted_user) -> None:
    client.force_login(restricted_user)
    response = client.get('/api/account/feed_id/')
    assert response.status_code == 200
    assert response.json()['feed_id'] == str(models.UserMisc.objects.get(user=restricted_user).feed_id)


@pytest.mark.django_db
def test_first_account_created_through_initial_setup_is_the_admin(client) -> None:
    response = client.post('/api/initial_setup/create_user/', data={
        'username': 'owner',
        'email': 'owner@example.com',
        'password': 'a-long-password',
    }, content_type='application/json')
    assert response.status_code == 201
    user = models.User.objects.get(username='owner')
    assert user.is_superuser and user.is_staff


@pytest.mark.django_db
def test_initial_setup_refuses_more_accounts(client, reader_user) -> None:
    client.post('/api/initial_setup/create_user/', data={'username': 'owner', 'password': 'a-long-password'},
                content_type='application/json')
    response = client.post('/api/initial_setup/create_user/',
                           data={'username': 'second', 'password': 'a-long-password'},
                           content_type='application/json')
    assert response.status_code == 400
@pytest.mark.django_db
def test_read_view_fixes_a_page_count_that_no_longer_matches_the_file(client, book, reader_user) -> None:
    book.page_count = 1  # left by an earlier scan of a different file
    book.save()
    client.force_login(reader_user)
    assert client.get(f'/api/read/{book.selector}/').json()['pages'] == 3
    book.refresh_from_db()
    assert book.page_count == 3


@pytest.mark.django_db
def test_pdf_action_serves_the_file(client, reader_user, comic_volume) -> None:
    make_pdf(comic_volume / 'issue.pdf', pages=2)
    book = models.ComicBook.objects.create(file_name='issue.pdf')
    client.force_login(reader_user)
    response = client.get(f'/api/read/{book.selector}/pdf/')
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'


@pytest.mark.django_db
def test_pdf_action_returns_404_when_the_file_is_not_on_disk(client, reader_user, comic_volume) -> None:
    book = models.ComicBook.objects.create(file_name='gone.pdf')
    client.force_login(reader_user)
    assert client.get(f'/api/read/{book.selector}/pdf/').status_code == 404


@pytest.mark.django_db
def test_type_action_reports_the_file_type(client, book, reader_user) -> None:
    client.force_login(reader_user)
    assert client.get(f'/api/read/{book.selector}/type/').json() == {'type': 'cbz'}


@pytest.mark.django_db
def test_set_page_rejects_a_page_that_is_not_a_number(client, book, reader_user) -> None:
    client.force_login(reader_user)
    response = client.put(f'/api/read/{book.selector}/set_page/', data={'page': 'x'}, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_history_search_matches_file_names(client, book, reader_user) -> None:
    client.force_login(reader_user)
    models.ComicStatus.objects.create(comic=book, user=reader_user, unread=False)
    assert client.get('/api/history/?search_text=issue').json()['count'] == 1
    assert client.get('/api/history/?search_text=writer').json()['count'] == 0


@pytest.mark.django_db
def test_account_password_reset_needs_the_logged_in_username(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/reset_password/', data={
        'username': 'someone-else',
        'old_password': 'password12345',
        'new_password': 'a-new-longer-password',
        'new_password_confirm': 'a-new-longer-password',
    }, content_type='application/json')
    assert response.status_code == 400
    assert response.json()['errors'] == 'Username does not match account'


@pytest.mark.django_db
def test_account_email_update_needs_the_logged_in_username(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/update_email/', data={
        'username': 'someone-else',
        'email': 'new@example.com',
        'password': 'password12345',
    }, content_type='application/json')
    assert response.status_code == 400
    assert response.json()['errors'] == 'Username does not match account'


@pytest.mark.django_db
def test_account_email_update_rejects_an_address_that_is_not_an_email(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.patch('/api/account/update_email/', data={
        'username': reader_user.username,
        'email': 'not-an-email',
        'password': 'password12345',
    }, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_mark_unread_rejects_selectors_that_are_not_uuids(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.put('/api/action/mark_unread/', data={'selectors': ['not-a-uuid']},
                          content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_directory_full_update_rejects_an_unknown_rating(client, admin_user) -> None:
    client.force_login(admin_user)
    directory = models.Directory.objects.create(name='Parent')
    response = client.put(f'/api/directory/{directory.selector}/', data={'classification': 9},
                          content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_scan_rejects_a_selector_that_is_not_a_uuid(client, reader_user) -> None:
    client.force_login(reader_user)
    response = client.post('/api/browse/scan/', data={'selector': 'not-a-uuid'}, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_initial_setup_reports_that_setup_is_needed_while_no_user_exists(client) -> None:
    assert client.get('/api/initial_setup/required/').json() == {'required': True}


@pytest.mark.django_db
def test_initial_setup_rejects_an_account_without_a_password(client) -> None:
    response = client.post('/api/initial_setup/create_user/', data={'username': 'owner'},
                           content_type='application/json')
    assert response.status_code == 400
@pytest.mark.django_db
def test_continue_reading_skips_books_above_the_users_allowance(client, book, restricted_user) -> None:
    client.force_login(restricted_user)
    models.ComicStatus.objects.create(comic=book, user=restricted_user, last_read_page=1)
    assert client.get('/api/read/continue/').json() == []


@pytest.mark.django_db
def test_continue_reading_skips_a_finished_book_that_is_the_last_issue_in_its_folder(client, book, reader_user) -> None:
    client.force_login(reader_user)
    models.ComicStatus.objects.create(comic=book, user=reader_user, last_read_page=2, unread=False, finished=True)
    assert client.get('/api/read/continue/').json() == []


@pytest.mark.django_db
def test_pdf_action_is_blocked_for_a_user_below_the_rating(client, book, restricted_user) -> None:
    client.force_login(restricted_user)
    assert client.get(f'/api/read/{book.selector}/pdf/').status_code == 403
