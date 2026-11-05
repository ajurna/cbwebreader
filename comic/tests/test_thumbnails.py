"""Tests for the thumbnail and page-image code paths of comic.models."""

import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from comic import models
from comic.tests.factories import make_cbz, make_pdf


@pytest.fixture()
def media_root(settings, comic_volume: Path) -> Path:
    """Keep the generated thumbnails out of the real MEDIA_ROOT."""
    root = comic_volume / 'media'
    root.mkdir()
    settings.MEDIA_ROOT = root
    return root


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
def test_get_pdf_points_at_the_file_in_the_directory_tree(comic_volume: Path) -> None:
    parent = models.Directory.objects.create(name='Series')
    child = models.Directory.objects.create(name='Volume 1', parent=parent)
    book = models.ComicBook.objects.create(file_name='issue.pdf', directory=child)

    assert book.get_pdf() == comic_volume / 'Series' / 'Volume 1' / 'issue.pdf'


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
    book = models.ComicBook.objects.create(file_name='broken.cbz')

    book.generate_thumbnail()
    book.refresh_from_db()

    assert not book.thumbnail
    assert list(media_root.glob('*')) == []
