import mimetypes
from itertools import chain
from pathlib import Path
from typing import NamedTuple, List

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q, F, Case, When, PositiveSmallIntegerField

from comic import models
from comic.errors import NotCompatibleArchive


def generate_directory(user: User, directory=None):
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
        finished=Q(total=F('progress')),
        unread=Q(total__gt=F('progress'))
    )
    files.extend(dir_db_query)

    # Create Missing Status
    new_status = [models.ComicStatus(comic=file, user=user) for file in
                  file_db_query.exclude(comicstatus__in=models.ComicStatus.objects.filter(
                      comic__in=file_db_query, user=user))]
    models.ComicStatus.objects.bulk_create(new_status)

    file_db_query = file_db_query.annotate(
        total=Count('comicpage', distinct=True),
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


def clean_directories(directories, dir_path, directory=None):
    dir_db_set = set([Path(settings.COMIC_BOOK_VOLUME, x.path) for x in directories])
    dir_list = set([x for x in sorted(dir_path.glob('*')) if x.is_dir()])
    # Create new directories db instances
    for new_directory in dir_list - dir_db_set:
        models.Directory(name=new_directory.name, parent=directory).save()

    # Remove stale db instances
    for stale_directory in dir_db_set - dir_list:
        models.Directory.objects.get(name=stale_directory.name, parent=directory).delete()


def clean_files(files, user, dir_path, directory=None):
    file_list = set([x for x in sorted(dir_path.glob('*')) if x.is_file()])
    files_db_set = set([Path(dir_path, x.file_name) for x in files])

    # Parse new comics
    books_to_add = []
    for new_comic in file_list - files_db_set:
        if new_comic.suffix.lower() in settings.SUPPORTED_FILES:
            books_to_add.append(
                models.ComicBook(file_name=new_comic.name, directory=directory)
            )
    models.ComicBook.objects.bulk_create(books_to_add)

    pages_to_add = []
    status_to_add = []
    for book in books_to_add:
        status_to_add.append(models.ComicStatus(user=user, comic=book))
        try:
            archive, archive_type = book.get_archive()
            if archive_type == 'archive':
                pages_to_add.extend([
                    models.ComicPage(
                        Comic=book, index=idx, page_file_name=page.file_name, content_type=page.mime_type
                    ) for idx, page in enumerate(get_archive_files(archive))
                ])
            elif archive_type == 'pdf':
                pages_to_add.extend([
                    models.ComicPage(
                        Comic=book, index=idx, page_file_name=idx + 1, content_type='application/pdf'
                    ) for idx in range(archive.page_count)
                ])
        except NotCompatibleArchive:
            pass

    models.ComicStatus.objects.bulk_create(status_to_add)
    models.ComicPage.objects.bulk_create(pages_to_add)

    # Remove stale comic instances
    for stale_comic in files_db_set - file_list:
        models.ComicBook.objects.get(file_name=stale_comic.name, directory=directory).delete()


class ArchiveFile(NamedTuple):
    file_name: str
    mime_type: str


def get_archive_files(archive) -> List[ArchiveFile]:
    return [
        ArchiveFile(x, mimetypes.guess_type(x)[0]) for x in sorted(archive.namelist())
        if not x.endswith('/') and mimetypes.guess_type(x)[0]
    ]
