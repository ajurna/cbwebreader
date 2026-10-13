"""Tests for the comic models."""

from pathlib import Path

import pytest
from django.db import IntegrityError

from comic import models
from comic.tests.factories import make_cbz, make_pdf


@pytest.mark.django_db
def test_page_count_excludes_metadata(comic_volume: Path) -> None:
    make_cbz(comic_volume / 'issue.cbz', pages=3, metadata=True)
    book = models.ComicBook.objects.create(file_name='issue.cbz')
    assert book.get_page_count() == 3


@pytest.mark.django_db
def test_pdf_page_count(comic_volume: Path) -> None:
    make_pdf(comic_volume / 'issue.pdf', pages=2)
    book = models.ComicBook.objects.create(file_name='issue.pdf')
    assert book.get_page_count() == 2


@pytest.mark.django_db
def test_unreadable_archive_is_indexed_without_pages(comic_volume: Path) -> None:
    path = comic_volume / 'broken.cbz'
    path.write_bytes(b'this is not an archive')
    result = models.ComicBook.process_comic_book(path)
    assert isinstance(result, Path)
    assert models.ComicBook.objects.get(file_name='broken.cbz').page_count == 0


@pytest.mark.django_db
def test_archive_path_uses_the_directory_tree(comic_volume: Path) -> None:
    parent = models.Directory.objects.create(name='Series')
    child = models.Directory.objects.create(name='Volume 1', parent=parent)
    book = models.ComicBook.objects.create(file_name='issue.cbz', directory=child)
    assert book.get_archive_path == comic_volume / 'Series' / 'Volume 1' / 'issue.cbz'


@pytest.mark.django_db
def test_book_without_a_directory_uses_the_volume_root(comic_volume: Path) -> None:
    book = models.ComicBook.objects.create(file_name='issue.cbz')
    assert book.get_archive_path == comic_volume / 'issue.cbz'


@pytest.mark.django_db
def test_directory_path_is_built_from_its_parents() -> None:
    parent = models.Directory.objects.create(name='Series')
    child = models.Directory.objects.create(name='Volume 1', parent=parent)
    assert child.get_path() == Path('Series') / 'Volume 1'


@pytest.mark.django_db
def test_get_image_returns_the_requested_page(comic_volume: Path) -> None:
    make_cbz(comic_volume / 'issue.cbz', pages=2, metadata=False)
    book = models.ComicBook.objects.create(file_name='issue.cbz')
    stream, mime_type = book.get_image(1)
    assert mime_type == 'image/png'
    assert stream.read()


@pytest.mark.django_db
def test_classification_comparison() -> None:
    directory = models.Directory.objects.create(name='Rated', classification=models.Directory.Classification.C_18)
    misc = models.UserMisc.objects.create(
        user=models.User.objects.create_user('pg', 'pg@example.com', 'password12345'),
        allowed_to_read=models.Directory.Classification.C_PG,
    )
    assert directory.classification > misc.allowed_to_read


@pytest.mark.django_db
def test_duplicate_directory_names_are_rejected() -> None:
    """The scan depends on this constraint: without it two concurrent requests can create
    the same directory twice and the browse listing shows it twice."""
    parent = models.Directory.objects.create(name='Series')
    models.Directory.objects.create(name='Volume 1', parent=parent)
    with pytest.raises(IntegrityError):
        models.Directory.objects.create(name='Volume 1', parent=parent)
