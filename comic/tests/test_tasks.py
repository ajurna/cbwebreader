"""Tests for the scan task."""

import pytest

from comic import models, tasks
from comic.tests.factories import make_cbz


@pytest.mark.django_db
def test_scan_task_runs_through_the_task_backend(comic_volume) -> None:
    """The immediate backend executes the task in the caller, so this is the whole path."""
    make_cbz(comic_volume / 'issue.cbz', pages=2)

    tasks.scan_directory.enqueue()

    assert models.ComicBook.objects.count() == 1
    assert models.ComicBook.objects.get().page_count == 2
