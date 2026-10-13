"""Tests for breadcrumb generation."""

import pytest

from comic import models
from comic.util import generate_breadcrumbs_from_path


@pytest.mark.django_db
def test_breadcrumbs_run_from_home_to_the_book() -> None:
    parent = models.Directory.objects.create(name='Series')
    child = models.Directory.objects.create(name='Volume 1', parent=parent)
    book = models.ComicBook.objects.create(file_name='issue.cbz', directory=child)
    assert [crumb.name for crumb in generate_breadcrumbs_from_path(child, book)] == [
        'Home', 'Series', 'Volume 1', 'issue.cbz',
    ]


@pytest.mark.django_db
def test_breadcrumbs_without_a_book_stop_at_the_directory() -> None:
    directory = models.Directory.objects.create(name='Series')
    assert [crumb.name for crumb in generate_breadcrumbs_from_path(directory)] == ['Home', 'Series']
