"""Tests for the scan_comics management command."""

from pathlib import Path

import pytest
from django.core.management import call_command

from comic import models
from comic.tests.factories import make_cbz


@pytest.mark.django_db
def test_scan_indexes_nested_directories(comic_volume: Path, reader_user) -> None:
    nested = comic_volume / 'Series' / 'Volume 1'
    nested.mkdir(parents=True)
    make_cbz(nested / 'issue.cbz', pages=2)

    call_command('scan_comics')

    directory = models.Directory.objects.get(name='Volume 1', parent__name='Series')
    book = models.ComicBook.objects.get(file_name='issue.cbz', directory=directory)
    assert book.page_count == 2


@pytest.mark.django_db
def test_scan_without_a_user_stops_before_reading_the_volume(comic_volume: Path) -> None:
    make_cbz(comic_volume / 'issue.cbz', pages=1)

    call_command('scan_comics')

    assert models.ComicBook.objects.count() == 0
