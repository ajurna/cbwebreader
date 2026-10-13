from collections.abc import Iterable
from pathlib import Path

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import (
    BooleanField,
    Case,
    Count,
    ExpressionWrapper,
    F,
    IntegerField,
    PositiveSmallIntegerField,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from comic import models
from comic.archives import get_archive_files
from comic.errors import NotCompatibleArchive


def reconcile(directory: models.Directory | None = None) -> None:
    """Bring the database in line with the filesystem for one directory.

    This is the only place the scan writes, so it runs from the scan task and the
    management command - never from a browse request.
    """
    dir_path = Path(settings.COMIC_BOOK_VOLUME, directory.path) if directory else settings.COMIC_BOOK_VOLUME

    clean_directories(models.Directory.objects.filter(parent=directory), dir_path, directory)
    clean_files(models.ComicBook.objects.filter(directory=directory), dir_path, directory)
    clean_thumbnails(models.Directory.objects.filter(parent=directory))
    clean_thumbnails(models.ComicBook.objects.filter(directory=directory))


def list_directory(user: AbstractBaseUser, directory: models.Directory | None = None) \
        -> list[models.Directory | models.ComicBook]:
    """Return the contents of one directory for one user, reading only."""
    dir_db_query = models.Directory.objects.filter(parent=directory).annotate(
        total=Count('comicbook', distinct=True),
        progress=Count('comicbook__comicstatus', Q(comicbook__comicstatus__finished=True,
                                                   comicbook__comicstatus__user=user), distinct=True),
        finished=ExpressionWrapper(Q(total=F('progress')), output_field=IntegerField()),
        unread=ExpressionWrapper(Q(total__gt=F('progress')), output_field=IntegerField()),
    )

    # A book with no status for this user is simply unread, so the annotations have to
    # stand in for the missing row instead of assuming one exists.
    file_db_query = models.ComicBook.objects.filter(directory=directory).annotate(
        progress=Coalesce(F('comicstatus__last_read_page') + 1, Value(0, output_field=IntegerField())),
        finished=Coalesce(F('comicstatus__finished'), Value(False, output_field=BooleanField())),
        unread=Coalesce(F('comicstatus__unread'), Value(True, output_field=BooleanField())),
        user=F('comicstatus__user'),
        classification=Case(
            When(directory__isnull=True, then=models.Directory.Classification.C_G),
            default=F('directory__classification'),
            output_field=PositiveSmallIntegerField(choices=models.Directory.Classification.choices)
        )
    ).filter(Q(user__isnull=True) | Q(user=user.id))

    files = list(dir_db_query) + list(file_db_query)
    files.sort(key=lambda x: x.title)
    files.sort(key=lambda x: x.type, reverse=True)
    return files


def clean_directories(directories: QuerySet, dir_path: Path, directory: models.Directory | None = None) -> None:
    dir_db_set = {Path(settings.COMIC_BOOK_VOLUME, x.path) for x in directories}
    dir_list = {x for x in sorted(dir_path.glob('*')) if x.is_dir()}
    # Create new directories db instances
    for new_directory in dir_list - dir_db_set:
        # get_or_create, not save(): another request may have inserted the same directory
        # between the query above and this line, which would leave duplicate rows.
        models.Directory.objects.get_or_create(name=new_directory.name, parent=directory)

    # Remove stale db instances
    for stale_directory in dir_db_set - dir_list:
        models.Directory.objects.filter(name=stale_directory.name, parent=directory).delete()


def clean_files(files: QuerySet, dir_path: Path, directory: models.Directory | None = None) -> None:
    file_list = {x for x in sorted(dir_path.glob('*')) if x.is_file()}
    files_db_set = {Path(dir_path, x.file_name) for x in files}

    # Parse new comics
    books_to_add = []
    for new_comic in file_list - files_db_set:
        if new_comic.suffix.lower() in settings.SUPPORTED_FILES:
            new_book = models.ComicBook(file_name=new_comic.name, directory=directory)
            try:
                archive, archive_type = new_book.get_archive()
                if archive_type == 'archive':
                    new_book.page_count = len(get_archive_files(archive))
                elif archive_type == 'pdf':
                    new_book.page_count = archive.page_count
            except NotCompatibleArchive:
                # Unreadable/corrupt archive - index the file with no page count
                pass
            books_to_add.append(new_book)

    # ignore_conflicts: a concurrent scan may have indexed the same file, and
    # (directory, file_name) is unique.
    models.ComicBook.objects.bulk_create(books_to_add, ignore_conflicts=True)

    # Remove stale comic instances
    for stale_comic in files_db_set - file_list:
        models.ComicBook.objects.filter(file_name=stale_comic.name, directory=directory).delete()


def clean_thumbnails(items: Iterable[models.Directory | models.ComicBook]) -> None:
    for item in items:
        if item.thumbnail and not Path(item.thumbnail.path).exists():
            item.thumbnail.delete()
            item.save()
