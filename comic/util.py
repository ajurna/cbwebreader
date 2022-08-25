from collections import OrderedDict
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Union, Iterable

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q, F, Case, When, PositiveSmallIntegerField
from django.utils.http import urlsafe_base64_encode

from .models import ComicBook, Directory, ComicStatus


def generate_title_from_path(file_path: Path):
    if file_path == "Home":
        return "CBWebReader"
    return f'CBWebReader - {" - ".join(p for p in file_path.parts)}'


class Menu:
    def __init__(self, user, page=""):
        """

        :type page: str
        """
        self.menu_items = OrderedDict()
        self.menu_items["Browse"] = "/comic/"
        self.menu_items["Recent"] = "/comic/recent/"
        self.menu_items["Account"] = "/comic/account/"
        if user.is_superuser:
            self.menu_items["Users"] = "/comic/settings/users/"
        self.menu_items["Logout"] = "/logout/"
        self.current_page = page


class Breadcrumb:
    def __init__(self):
        self.name = "Home"
        self.url = "/comic/"
        self.selector = ''

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


def generate_breadcrumbs_from_path(directory=False, book=False):
    """

    :type directory: Directory
    :type book: ComicBook
    """
    output = [Breadcrumb()]
    if directory:
        folders = directory.get_path_objects()
    else:
        folders = []
    for item in folders[::-1]:
        bc = Breadcrumb()
        bc.name = item.name
        bc.url = "/comic/" + urlsafe_base64_encode(item.selector.bytes)
        bc.selector = item.selector
        output.append(bc)
    if book:
        bc = Breadcrumb()
        bc.name = book.file_name
        bc.url = "/read/" + urlsafe_base64_encode(book.selector.bytes)
        bc.selector = book.selector
        output.append(bc)

    return output


def generate_breadcrumbs_from_menu(paths):
    output = [Breadcrumb()]
    for item in paths:
        bc = Breadcrumb()
        bc.name = item[0]
        bc.url = item[1]
        output.append(bc)
    return output


@dataclass
class DirFile:
    obj: Union[Directory, ComicBook]
    name: str = ''
    item_type: str = ''
    percent: int = 0
    selector: str = ''
    total: int = 0
    total_read: int = 0
    total_unread: int = 0

    def __post_init__(self):
        self.item_type = type(self.obj).__name__
        if hasattr(self.obj, 'total') and hasattr(self.obj, 'total_read'):
            # because pages count from zero.
            total_adjustment = 1
            if isinstance(self.obj, Directory):
                total_adjustment = 0
            self.total = self.obj.total - total_adjustment
            self.total_read = self.obj.total_read
            self.total_unread = self.total - self.total_read
            try:
                self.percent = int((self.obj.total_read / self.total) * 100)
            except ZeroDivisionError:
                self.percent = 0

        self.selector = self.obj.url_safe_selector
        if isinstance(self.obj, Directory):
            self.name = self.obj.name
        elif isinstance(self.obj, ComicBook):
            self.name = self.obj.file_name
    @property
    def type(self):
        return 'ComicBook'

    @property
    def title(self):
        return self.name

    @property
    def progress(self):
        return self.total_read

    @property
    def thumbnail(self):
        return '/error.jpg'

def generate_directory(user: User, directory=None):
    """
    :type user: User
    :type directory: Directory
    """
    base_dir = settings.COMIC_BOOK_VOLUME
    files = []
    dir_path = Path(base_dir, directory.path) if directory else base_dir
    dir_list = [x for x in sorted(dir_path.glob('*')) if x.is_dir()]

    file_list = [x for x in sorted(dir_path.glob('*')) if x.is_file()]
    dir_list_obj = Directory.objects.filter(name__in=[x.name for x in dir_list], parent=directory)
    file_list_obj = ComicBook.objects.filter(file_name__in=[x.name for x in file_list], directory=directory)

    for file in chain(file_list_obj, dir_list_obj):
        if file.thumbnail and not Path(file.thumbnail.path).exists():
            file.thumbnail.delete()
            file.save()

    dir_list_obj = dir_list_obj.annotate(
        total=Count('comicbook', distinct=True),
        total_read=Count('comicbook__comicstatus', Q(comicbook__comicstatus__finished=True,
                                                     comicbook__comicstatus__user=user), distinct=True)
    )

    # Create Missing Status
    status_list = [x.comic for x in
                   ComicStatus.objects.filter(comic__in=file_list_obj, user=user).select_related('comic')]
    new_status = [ComicStatus(comic=file, user=user) for file in file_list_obj if file not in status_list]
    ComicStatus.objects.bulk_create(new_status)

    file_list_obj = file_list_obj.annotate(
        total=Count('comicpage', distinct=True),
        total_read=F('comicstatus__last_read_page'),
        finished=F('comicstatus__finished'),
        unread=F('comicstatus__unread'),
        user=F('comicstatus__user'),
        classification=Case(
            When(directory__isnull=True, then=Directory.Classification.C_18),
            default=F('directory__classification'),
            output_field=PositiveSmallIntegerField(choices=Directory.Classification.choices)
        )
    ).filter(Q(user__isnull=True) | Q(user=user.id))

    for directory_obj in dir_list_obj:
        files.append(DirFile(directory_obj))
        dir_list.remove(Path(dir_path, directory_obj.name))

    for file_obj in file_list_obj:
        files.append(DirFile(file_obj))
        file_list.remove(Path(dir_path, file_obj.file_name))

    for directory_name in dir_list:
        if directory:
            directory_obj = Directory(name=directory_name.name, parent=directory)
        else:
            directory_obj = Directory(name=directory_name.name)
        directory_obj.save()
        directory_obj.total = 0
        directory_obj.total_read = 0
        files.append(DirFile(directory_obj))
    files = [file for file in files if file.obj.classification <= user.usermisc.allowed_to_read]

    comics_to_annotate = []
    for file_name in file_list:
        if file_name.suffix.lower() in [".rar", ".zip", ".cbr", ".cbz", ".pdf"]:
            book = ComicBook.process_comic_book(file_name, directory)
            ComicStatus(user=user, comic=book).save()
            comics_to_annotate.append(book.selector)
    if comics_to_annotate:
        new_comics = ComicBook.objects.filter(selector__in=comics_to_annotate).annotate(
                total=Count('comicpage', distinct=True),
                total_read=F('comicstatus__last_read_page'),
                finished=F('comicstatus__finished'),
                unread=F('comicstatus__unread'),
                user=F('comicstatus__user'),
                classification=Case(
                    When(directory__isnull=True, then=Directory.Classification.C_18),
                    default=F('directory__classification'),
                    output_field=PositiveSmallIntegerField(choices=Directory.Classification.choices)
                )
            ).filter(Q(user__isnull=True) | Q(user=user.id))

        files.extend([DirFile(b) for b in new_comics])
    files.sort(key=lambda x: x.name)
    files.sort(key=lambda x: x.item_type, reverse=True)
    return files


def generate_label(book):
    """
    book need to be annotated with the following from ComicStatus
        * unread
        * finished
        * last_read_page
        * total_pages
    :param book: ComicBook
    :return: str
    """
    unread_text = '<center><span class="label label-default">Unread</span></center>'
    if not hasattr(book, 'unread'):
        label_text = unread_text
    elif book.unread or book.unread is None:
        label_text = unread_text
    elif book.finished:
        label_text = '<center><span class="label label-success">Read</span></center>'
    else:
        label_text = '<center><span class="label label-primary">%s/%s</span></center>' % (
            book.last_read_page + 1,
            book.total_pages,
        )
    return label_text


def generate_dir_status(total, total_read):
    if total == 0:
        return '<center><span class="label label-default">Empty</span></center>'
    elif total == total_read:
        return '<center><span class="label label-success">All Read</span></center>'
    elif total_read == 0:
        return '<center><span class="label label-default">Unread</span></center>'
    return f'<center><span class="label label-primary">{total_read}/{total}</span></center>'
