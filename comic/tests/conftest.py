"""Shared fixtures for the test suite."""

from pathlib import Path

import pytest

from comic import models
from comic.tests.factories import make_cbz


@pytest.fixture()
def comic_volume(settings, tmp_path) -> Path:
    """Point COMIC_BOOK_VOLUME at an empty temporary directory."""
    settings.COMIC_BOOK_VOLUME = tmp_path
    return tmp_path


@pytest.fixture()
def admin_user(db) -> models.User:
    return models.User.objects.create_superuser('admin', 'admin@example.com', 'password12345')


@pytest.fixture()
def reader_user(db) -> models.User:
    """A normal user, whose reading allowance defaults to the highest rating."""
    return models.User.objects.create_user('reader', 'reader@example.com', 'password12345')


@pytest.fixture()
def restricted_user(db) -> models.User:
    """A user whose allowance is G, so anything rated above G is blocked."""
    user = models.User.objects.create_user('restricted', 'restricted@example.com', 'password12345')
    models.UserMisc.objects.create(user=user, allowed_to_read=models.Directory.Classification.C_G)
    return user


@pytest.fixture()
def rated_directory(db) -> models.Directory:
    return models.Directory.objects.create(name='Rated', classification=models.Directory.Classification.C_18)


@pytest.fixture()
def book(db, comic_volume: Path, rated_directory: models.Directory) -> models.ComicBook:
    """A book with a three page archive inside an 18 rated directory."""
    directory_path = comic_volume / rated_directory.name
    directory_path.mkdir(parents=True, exist_ok=True)
    make_cbz(directory_path / 'issue.cbz', pages=3)
    return models.ComicBook.objects.create(file_name='issue.cbz', directory=rated_directory, page_count=3)
