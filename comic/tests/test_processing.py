"""Tests for the filesystem reconciliation in comic.processing."""

import pytest

from comic import models
from comic.processing import clean_directories, clean_files, generate_directory
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

    clean_files(models.ComicBook.objects.filter(directory=directory), reader_user, target, directory)

    books = list(models.ComicBook.objects.filter(directory=directory))
    assert [book.file_name for book in books] == ['issue.cbz']
    assert books[0].page_count == 2
    assert models.ComicStatus.objects.filter(user=reader_user).count() == 1


@pytest.mark.django_db
def test_generate_directory_creates_missing_statuses(comic_volume, reader_user) -> None:
    directory = models.Directory.objects.create(name='Series')
    target = comic_volume / 'Series'
    target.mkdir(parents=True)
    make_cbz(target / 'issue.cbz', pages=1)

    entries = generate_directory(reader_user, directory)

    assert [entry.title for entry in entries] == ['issue.cbz']
    assert models.ComicStatus.objects.filter(user=reader_user, comic=entries[0]).exists()
