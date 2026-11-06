"""Tests for the thumbnail and page-image code paths of comic.models."""

import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from comic import models
from comic.tests.factories import make_cbz, make_pdf


def image_page() -> bytes:
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10)).save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.mark.django_db
def test_pdf_pages_are_returned_as_png(comic_volume: Path) -> None:
    make_pdf(comic_volume / 'issue.pdf', pages=2)
    book = models.ComicBook.objects.create(file_name='issue.pdf')

    stream, mime_type = book.get_image(1)

    assert mime_type == 'Image/PNG'
    assert Image.open(stream).size == (10, 10)


@pytest.mark.django_db
def test_get_image_returns_false_for_a_corrupt_archive(comic_volume: Path) -> None:
    (comic_volume / 'broken.cbz').write_bytes(b'this is not an archive')
    book = models.ComicBook.objects.create(file_name='broken.cbz')

    assert book.get_image(0) == (False, False)


@pytest.mark.django_db
def test_get_image_returns_false_for_a_page_outside_the_document(comic_volume: Path) -> None:
    make_cbz(comic_volume / 'issue.cbz', pages=2)
    make_pdf(comic_volume / 'issue.pdf', pages=2)

    assert models.ComicBook.objects.create(file_name='issue.cbz').get_image(2) == (False, False)
    assert models.ComicBook.objects.create(file_name='issue.pdf').get_image(2) == (False, False)


@pytest.mark.django_db
def test_get_image_returns_false_for_a_file_that_is_not_a_pdf(comic_volume: Path, media_root: Path) -> None:
    (comic_volume / 'broken.pdf').write_bytes(b'this is not a pdf')
    book = models.ComicBook.objects.create(file_name='broken.pdf')

    assert book.get_image(0) == (False, False)

    book.generate_thumbnail()
    book.refresh_from_db()
    assert not book.thumbnail


@pytest.mark.django_db
def test_generate_thumbnail_writes_a_resized_jpeg_for_an_archive(comic_volume: Path, media_root: Path) -> None:
    make_cbz(comic_volume / 'issue.cbz', pages=2)
    book = models.ComicBook.objects.create(file_name='issue.cbz', page_count=2)

    book.generate_thumbnail()
    book.refresh_from_db()

    assert book.thumbnail.name.endswith('.jpg')
    with Image.open(media_root / book.thumbnail.name) as image:
        assert image.format == 'JPEG'
        assert image.size == (200, 300)


@pytest.mark.django_db
def test_generate_thumbnail_writes_a_resized_jpeg_for_a_pdf(comic_volume: Path, media_root: Path) -> None:
    make_pdf(comic_volume / 'issue.pdf', pages=2)
    book = models.ComicBook.objects.create(file_name='issue.pdf')

    book.generate_thumbnail(1)
    book.refresh_from_db()

    with Image.open(media_root / book.thumbnail.name) as image:
        assert image.format == 'JPEG'
        assert image.size == (200, 300)


@pytest.mark.django_db
def test_generate_thumbnail_skips_archive_entries_that_are_not_images(
        comic_volume: Path, media_root: Path) -> None:
    with zipfile.ZipFile(comic_volume / 'issue.cbz', 'w') as archive:
        archive.writestr('page00.jpg', b'this is not an image')
        archive.writestr('page01.png', image_page())
    book = models.ComicBook.objects.create(file_name='issue.cbz', page_count=2)

    book.generate_thumbnail()
    book.refresh_from_db()

    assert book.thumbnail


@pytest.mark.django_db
def test_generate_thumbnail_writes_nothing_for_an_unreadable_archive(
        comic_volume: Path, media_root: Path) -> None:
    (comic_volume / 'broken.cbz').write_bytes(b'this is not an archive')
    # page_count comes from an earlier scan, so a book can have pages recorded and a
    # corrupt file on disk. Without it the loop body never runs and the file is never opened.
    book = models.ComicBook.objects.create(file_name='broken.cbz', page_count=1)

    book.generate_thumbnail()
    book.generate_thumbnail(1)  # the explicit page branch hits the same guard
    book.refresh_from_db()

    assert not book.thumbnail
    assert list(media_root.glob('*')) == []


@pytest.mark.django_db
def test_directory_thumbnail_copies_the_thumbnail_of_its_first_book(
        comic_volume: Path, media_root: Path) -> None:
    directory = models.Directory.objects.create(name='Series')
    (comic_volume / 'Series').mkdir()
    make_cbz(comic_volume / 'Series' / 'issue.cbz', pages=2)
    book = models.ComicBook.objects.create(file_name='issue.cbz', directory=directory, page_count=2)

    directory.generate_thumbnail()
    directory.refresh_from_db()
    book.refresh_from_db()

    assert directory.thumbnail.name == book.thumbnail.name


@pytest.mark.django_db
def test_directory_thumbnail_writes_nothing_for_an_empty_directory(
        comic_volume: Path, media_root: Path) -> None:
    directory = models.Directory.objects.create(name='Empty')

    directory.generate_thumbnail()
    directory.refresh_from_db()

    assert not directory.thumbnail
    assert list(media_root.glob('*')) == []
