import mimetypes
import zipfile
from itertools import chain
from pathlib import Path
from typing import NamedTuple, List, Optional, Union

import rarfile
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Count, Q, F, Case, When, PositiveSmallIntegerField, QuerySet, ExpressionWrapper, \
    IntegerField

from comic import models
from comic.errors import NotCompatibleArchive


def generate_directory(user: AbstractBaseUser, directory: Optional[models.Directory] = None) \
        -> List[Union[models.Directory, models.ComicBook]]:
    dir_path = Path(settings.COMIC_BOOK_VOLUME, directory.path) if directory else settings.COMIC_BOOK_VOLUME
    files = []

    dir_db_query = models.Directory.objects.filter(parent=directory)
    clean_directories(dir_db_query, dir_path, directory)

    file_db_query = models.ComicBook.objects.filter(directory=directory)
    clean_files(file_db_query, user, dir_path, directory)

    dir_db_query = dir_db_query.annotate(
        total=Count('comicbook', distinct=True),
        progress=Count('comicbook__comicstatus', Q(comicbook__comicstatus__finished=True,
                                                   comicbook__comicstatus__user=user), distinct=True),
        finished=ExpressionWrapper(Q(total=F('progress')), output_field=IntegerField()),
        unread=ExpressionWrapper(Q(total__gt=F('progress')), output_field=IntegerField()),
    )
    files.extend(dir_db_query)

    # Create Missing Status
    new_status = [models.ComicStatus(comic=file, user=user) for file in
                  file_db_query.exclude(comicstatus__in=models.ComicStatus.objects.filter(
                      comic__in=file_db_query, user=user))]
    models.ComicStatus.objects.bulk_create(new_status)

    file_db_query = file_db_query.annotate(
        progress=F('comicstatus__last_read_page') + 1,
        finished=F('comicstatus__finished'),
        unread=F('comicstatus__unread'),
        user=F('comicstatus__user'),
        classification=Case(
            When(directory__isnull=True, then=models.Directory.Classification.C_G),
            default=F('directory__classification'),
            output_field=PositiveSmallIntegerField(choices=models.Directory.Classification.choices)
        )
    ).filter(Q(user__isnull=True) | Q(user=user.id))

    files.extend(file_db_query)

    for file in chain(file_db_query, dir_db_query):
        if file.thumbnail and not Path(file.thumbnail.path).exists():
            file.thumbnail.delete()
            file.save()
    files.sort(key=lambda x: x.title)
    files.sort(key=lambda x: x.type, reverse=True)
    return files


def clean_directories(directories: QuerySet, dir_path: Path, directory: Optional[models.Directory] = None) -> None:
    dir_db_set = set(Path(settings.COMIC_BOOK_VOLUME, x.path) for x in directories)
    dir_list = set(x for x in sorted(dir_path.glob('*')) if x.is_dir())
    # Create new directories db instances
    for new_directory in dir_list - dir_db_set:
        models.Directory(name=new_directory.name, parent=directory).save()

    # Remove stale db instances
    for stale_directory in dir_db_set - dir_list:
        models.Directory.objects.get(name=stale_directory.name, parent=directory).delete()


def clean_files(files: QuerySet, user: AbstractBaseUser, dir_path: Path, directory: Optional[models.Directory] = None) \
        -> None:
    file_list = set(x for x in sorted(dir_path.glob('*')) if x.is_file())
    files_db_set = set(Path(dir_path, x.file_name) for x in files)

    # Parse new comics
    books_to_add = []
    for new_comic in file_list - files_db_set:
        if new_comic.suffix.lower() in settings.SUPPORTED_FILES:
            new_book = models.ComicBook(file_name=new_comic.name, directory=directory)
            archive, archive_type = new_book.get_archive()
            try:
                if archive_type == 'archive':
                    new_book.page_count = len(get_archive_files(archive))
                elif archive_type == 'pdf':
                    new_book.page_count = archive.page_count
            except NotCompatibleArchive:
                pass
            books_to_add.append(new_book)
    models.ComicBook.objects.bulk_create(books_to_add)

    status_to_add = []
    for book in books_to_add:
        status_to_add.append(models.ComicStatus(user=user, comic=book))

    models.ComicStatus.objects.bulk_create(status_to_add)

    # Remove stale comic instances
    for stale_comic in files_db_set - file_list:
        models.ComicBook.objects.get(file_name=stale_comic.name, directory=directory).delete()


class ArchiveFile(NamedTuple):
    file_name: str
    mime_type: str


def get_archive_files(archive: Union[zipfile.ZipFile, rarfile.RarFile]) -> List[ArchiveFile]:
    return [
        ArchiveFile(x, mimetypes.guess_type(x)[0]) for x in sorted(archive.namelist())
        if not x.endswith('/') and mimetypes.guess_type(x)[0]
    ]
