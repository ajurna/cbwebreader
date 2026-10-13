"""Tests for the filesystem reconciliation in comic.processing."""

import pytest

from comic import models
from comic.processing import clean_directories, clean_files, list_directory, reconcile
from comic.tests.factories import make_cbz


@pytest.mark.django_db
def test_clean_directories_adds_new_and_removes_stale(comic_volume, reader_user) -> None:
    parent = models.Directory.objects.create(name='Series')
    models.Directory.objects.create(name='Gone', parent=parent)
    (comic_volume / 'Series' / 'New').mkdir(parents=True)

    clean_directories(models.Directory.objects.filter(parent=parent), comic_volume / 'Series', parent)

    names = set(models.Directory.objects.filter(parent=parent).values_list('name', flat=True))
    assert names == {'New'}


@pytest.mark.django_db
def test_clean_files_ignores_unsupported_extensions(comic_volume, reader_user) -> None:
    directory = models.Directory.objects.create(name='Series')
    target = comic_volume / 'Series'
    target.mkdir(parents=True)
    make_cbz(target / 'issue.cbz', pages=2)
    (target / 'notes.txt').write_text('not a comic')

    clean_files(models.ComicBook.objects.filter(directory=directory), target, directory)

    books = list(models.ComicBook.objects.filter(directory=directory))
    assert [book.file_name for book in books] == ['issue.cbz']
    assert books[0].page_count == 2


@pytest.mark.django_db
def test_reconcile_indexes_the_directory_without_touching_the_database_on_a_second_run(
        comic_volume, reader_user) -> None:
    directory = models.Directory.objects.create(name='Series')
    target = comic_volume / 'Series'
    target.mkdir(parents=True)
    make_cbz(target / 'issue.cbz', pages=2)

    reconcile(directory)
    first = list(models.ComicBook.objects.filter(directory=directory))
    assert [book.file_name for book in first] == ['issue.cbz']

    reconcile(directory)
    assert list(models.ComicBook.objects.filter(directory=directory)) == first


@pytest.mark.django_db
def test_list_directory_reports_an_unread_book_without_creating_a_status(comic_volume,
                                                                         reader_user) -> None:
    """Listing is read only: a book nobody has opened has no ComicStatus row at all."""
    directory = models.Directory.objects.create(name='Series')
    target = comic_volume / 'Series'
    target.mkdir(parents=True)
    make_cbz(target / 'issue.cbz', pages=3)
    reconcile(directory)

    entries = list_directory(reader_user, directory)

    assert [entry.title for entry in entries] == ['issue.cbz']
    assert entries[0].progress == 0
    assert entries[0].unread is True
    assert entries[0].finished is False
    assert models.ComicStatus.objects.count() == 0


@pytest.mark.django_db
def test_list_directory_shows_progress_for_a_book_that_has_been_read(comic_volume,
                                                                     reader_user) -> None:
    directory = models.Directory.objects.create(name='Series')
    target = comic_volume / 'Series'
    target.mkdir(parents=True)
    make_cbz(target / 'issue.cbz', pages=3)
    reconcile(directory)
    book = models.ComicBook.objects.get(directory=directory)
    models.ComicStatus.objects.create(user=reader_user, comic=book, last_read_page=1, unread=False)

    entries = list_directory(reader_user, directory)

    assert entries[0].progress == 2
    assert entries[0].unread is False
    assert entries[0].finished is False


@pytest.mark.django_db
def test_clean_files_survives_a_concurrent_scan_of_the_same_directory(comic_volume, reader_user,
                                                                      rated_directory) -> None:
    """Two requests can build the same 'new file' list; the second insert must not clash."""
    target = comic_volume / rated_directory.name
    target.mkdir(parents=True, exist_ok=True)
    make_cbz(target / 'issue.cbz', pages=2)

    stale = models.ComicBook.objects.filter(directory=rated_directory)
    list(stale)  # force evaluation so the cached snapshot is empty
    models.ComicBook.objects.create(file_name='issue.cbz', directory=rated_directory, page_count=2)

    clean_files(stale, target, rated_directory)

    assert models.ComicBook.objects.filter(directory=rated_directory).count() == 1


@pytest.mark.django_db
def test_clean_files_ignores_rows_another_request_already_removed(comic_volume, reader_user,
                                                                  rated_directory) -> None:
    target = comic_volume / rated_directory.name
    target.mkdir(parents=True, exist_ok=True)
    stale_book = models.ComicBook.objects.create(file_name='gone.cbz', directory=rated_directory)

    stale = models.ComicBook.objects.filter(directory=rated_directory)
    list(stale)  # cache the row, then let another request delete it
    stale_book.delete()

    clean_files(stale, target, rated_directory)

    assert models.ComicBook.objects.filter(directory=rated_directory).count() == 0


@pytest.mark.django_db
def test_clean_directories_does_not_duplicate_rows_when_another_request_inserts_first(comic_volume,
                                                                                     reader_user) -> None:
    parent = models.Directory.objects.create(name='Series')
    (comic_volume / 'Series' / 'New').mkdir(parents=True)

    stale = models.Directory.objects.filter(parent=parent)
    list(stale)  # cached snapshot is empty
    models.Directory.objects.create(name='New', parent=parent)

    clean_directories(stale, comic_volume / 'Series', parent)

    assert models.Directory.objects.filter(parent=parent).count() == 1
