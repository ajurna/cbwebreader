"""The folder scan as a task.

The default backend runs tasks immediately, so this behaves like a function call today.
Writing it as a task is what lets the scan move to a worker later without changing any
of the call sites in comic/rest.py or the management command.
"""

from django.tasks import task

from comic import models
from comic.processing import reconcile


@task
def scan_directory(selector: str | None = None) -> None:
    """Reconcile one directory, or the root of the comic volume when no selector is given."""
    directory = models.Directory.objects.filter(selector=selector).first() if selector else None
    reconcile(directory)
