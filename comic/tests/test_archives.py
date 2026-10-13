"""Tests for the shared archive page listing in comic.archives."""

import zipfile
from pathlib import Path

from comic.archives import get_archive_files
from comic.tests.factories import make_cbz


def names(archive: zipfile.ZipFile) -> list[str]:
    return [entry.file_name for entry in get_archive_files(archive)]


def test_metadata_entries_are_not_pages(tmp_path: Path) -> None:
    path = make_cbz(tmp_path / 'issue.cbz', pages=2, metadata=True)
    with zipfile.ZipFile(path) as archive:
        assert names(archive) == ['page00.png', 'page01.png']


def test_entries_are_returned_in_page_order(tmp_path: Path) -> None:
    path = tmp_path / 'issue.cbz'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('page10.png', b'x')
        archive.writestr('page02.png', b'x')
        archive.writestr('page01.png', b'x')
    with zipfile.ZipFile(path) as archive:
        assert names(archive) == ['page01.png', 'page02.png', 'page10.png']


def test_directory_entries_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / 'issue.cbz'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('cover.png', b'x')
        archive.writestr('images/', b'')
    with zipfile.ZipFile(path) as archive:
        assert names(archive) == ['cover.png']


def test_mime_type_is_guessed_from_the_file_name(tmp_path: Path) -> None:
    path = make_cbz(tmp_path / 'issue.cbz', pages=1, metadata=False)
    with zipfile.ZipFile(path) as archive:
        assert get_archive_files(archive)[0].mime_type == 'image/png'
