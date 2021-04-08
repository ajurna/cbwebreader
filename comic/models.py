import uuid
import zipfile
from dataclasses import dataclass
from functools import reduce
from os import listdir
from pathlib import Path
from typing import Optional, List

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.transaction import atomic
from django.utils.http import urlsafe_base64_encode
import PyPDF4
import PyPDF4.utils


import rarfile

if settings.UNRAR_TOOL:
    rarfile.UNRAR_TOOL = settings.UNRAR_TOOL


class Setting(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return '"%s":"%s"' % (self.name, self.value)

    def __unicode__(self):
        return self.__str__()


class Directory(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("Directory", null=True, blank=True, on_delete=models.CASCADE)
    selector = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "Directory: {0}; {1}".format(self.name, self.parent)

    @property
    def path(self) -> Path:
        return self.get_path()

    def get_path(self) -> Path:
        path_items = self.get_path_items()
        path_items.reverse()
        if len(path_items) >= 2:
            return reduce(lambda x, y: Path(x, y), path_items)
        else:
            return Path(path_items[0])

    def get_path_items(self, p: Optional[List] = None) -> List[str]:
        if p is None:
            p = []
        p.append(self.name)
        if self.parent:
            self.parent.get_path_items(p)
        return p

    def get_path_objects(self, p=None):
        if p is None:
            p = []
        p.append(self)
        if self.parent:
            self.parent.get_path_objects(p)
        return p

    # @staticmethod
    # def get_dir_from_path(file_path):
    #     file_path = file_path.split(os_path.sep)
    #     print(file_path)
    #     for d in Directory.objects.filter(name=file_path[-1]):
    #         print(d)
    #         if d.get_path_items() == file_path:
    #             return d


class ComicBook(models.Model):
    file_name = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    directory = models.ForeignKey(Directory, blank=True, null=True, on_delete=models.CASCADE)
    selector = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    version = models.IntegerField(default=1)

    def __str__(self):
        return self.file_name

    @property
    def selector_string(self):
        return urlsafe_base64_encode(self.selector.bytes)

    def get_pdf(self):
        base_dir = settings.COMIC_BOOK_VOLUME
        return Path(base_dir, self.directory.get_path(), self.file_name)

    def get_image(self, page: int):
        base_dir = settings.COMIC_BOOK_VOLUME
        if self.directory:
            archive_path = Path(base_dir, self.directory.path, self.file_name)
        else:
            archive_path = Path(base_dir, self.file_name)
        try:
            archive = rarfile.RarFile(archive_path)
        except rarfile.NotRarFile:
            archive = zipfile.ZipFile(archive_path)
        except zipfile.BadZipfile:
            return False
        page_obj = ComicPage.objects.get(Comic=self, index=page)
        try:
            out = (archive.open(page_obj.page_file_name), page_obj.content_type)
        except rarfile.NoRarEntry:
            ComicPage.objects.filter(Comic=self).delete()
            self.process_comic_pages(archive, self)
            out = self.get_image(page)
        return out

    def is_last_page(self, page):
        if (self.page_count - 1) == page:
            return True
        return False

    @property
    def page_count(self):
        return ComicPage.objects.filter(Comic=self).count()

    @dataclass
    class Navigation:
        next_path: str
        prev_path: str
        cur_path: str

    def nav(self, user):
        return self.Navigation(
            next_path=self.nav_get_next_comic(user),
            prev_path=self.nav_get_prev_comic(user),
            cur_path=urlsafe_base64_encode(self.selector.bytes)
        )

    def nav_get_prev_comic(self, user) -> str:
        base_dir = settings.COMIC_BOOK_VOLUME
        if self.directory:
            folder = Path(base_dir, self.directory.path)
        else:
            folder = base_dir
        dir_list = ComicBook.get_ordered_dir_list(folder)
        comic_index = dir_list.index(self.file_name)
        if comic_index == 0:
            if self.directory:
                comic_path = urlsafe_base64_encode(self.directory.selector.bytes)
            else:
                comic_path = ""
        else:
            prev_comic = dir_list[comic_index - 1]

            if Path(folder, prev_comic).is_dir():
                if self.directory:
                    comic_path = urlsafe_base64_encode(self.directory.selector.bytes)
                else:
                    comic_path = ""
            else:
                try:
                    if self.directory:
                        book = ComicBook.objects.get(file_name=prev_comic, directory=self.directory)
                    else:
                        book = ComicBook.objects.get(file_name=prev_comic, directory__isnull=True)
                except ComicBook.DoesNotExist:
                    if self.directory:
                        book = ComicBook.process_comic_book(prev_comic, self.directory)
                    else:
                        book = ComicBook.process_comic_book(prev_comic)
                cs, _ = ComicStatus.objects.get_or_create(comic=book, user=user)
                comic_path = urlsafe_base64_encode(book.selector.bytes)

        return comic_path

    def nav_get_next_comic(self, user):
        base_dir = settings.COMIC_BOOK_VOLUME
        if self.directory:
            folder = Path(base_dir, self.directory.path)
        else:
            folder = base_dir
        dir_list = ComicBook.get_ordered_dir_list(folder)
        comic_index = dir_list.index(self.file_name)
        try:
            next_comic = dir_list[comic_index + 1]
            try:
                if self.directory:
                    book = ComicBook.objects.get(file_name=next_comic, directory=self.directory)
                else:
                    book = ComicBook.objects.get(file_name=next_comic, directory__isnull=True)
            except ComicBook.DoesNotExist:
                if self.directory:
                    book = ComicBook.process_comic_book(next_comic, self.directory)
                else:
                    book = ComicBook.process_comic_book(next_comic)
            except ComicBook.MultipleObjectsReturned:
                if self.directory:
                    books = ComicBook.objects.filter(file_name=next_comic, directory=self.directory).order_by('id')
                else:
                    books = ComicBook.objects.get(file_name=next_comic, directory__isnull=True).order_by('id')
                book = books.first()
                books = books.exclude(id=book.id)
                books.delete()
            if type(book) is str:
                raise IndexError
            comic_path = urlsafe_base64_encode(book.selector.bytes)
        except IndexError:
            if self.directory:
                comic_path = urlsafe_base64_encode(self.directory.selector.bytes)
            else:
                comic_path = ""
        return comic_path

    class DirFile:
        def __init__(self):
            self.name = ""
            self.isdir = False
            self.icon = ""
            self.iscb = False
            self.location = ""
            self.label = ""
            self.cur_page = 0

        def __str__(self):
            return self.name

    @property
    def pages(self):
        return [cp for cp in ComicPage.objects.filter(Comic=self).order_by("index")]

    def page_name(self, index):
        return ComicPage.objects.get(Comic=self, index=index).page_file_name

    @staticmethod
    def process_comic_book(comic_file_name, directory=False):
        """

        :type comic_file_name: str
        :type directory: Directory
        """
        try:
            book = ComicBook.objects.get(file_name=comic_file_name, version=0)
            book.directory = directory
            book.version = 1
            book.save()
            return book
        except ComicBook.DoesNotExist:
            pass
        base_dir = settings.COMIC_BOOK_VOLUME
        if directory:
            comic_full_path = Path(base_dir, directory.get_path(), comic_file_name)
        else:
            comic_full_path = Path(base_dir, comic_file_name)

        try:
            cbx = rarfile.RarFile(comic_full_path)
        except rarfile.NotRarFile:
            cbx = None
        if not cbx:
            try:
                cbx = zipfile.ZipFile(comic_full_path)
            except zipfile.BadZipFile:
                cbx = None
        pdf_file = None
        if not cbx:
            try:
                pdf_file = PyPDF4.PdfFileReader(str(comic_full_path))
            except PyPDF4.utils.PyPdfError:
                pass
        if not pdf_file and not cbx:
            return comic_file_name


        if directory:
            book = ComicBook(file_name=comic_file_name, directory=directory)
        else:
            book = ComicBook(file_name=comic_file_name)
        book.save()
        page_index = 0
        if cbx:
            ComicBook.process_comic_pages(cbx, book)
        elif pdf_file:
            with atomic():
                for page_index in range(pdf_file.getNumPages()):
                    page = ComicPage(
                        Comic=book, index=page_index, page_file_name=page_index+1, content_type='application/pdf'
                    )
                    page.save()
        return book

    @staticmethod
    def process_comic_pages(cbx, book):
        with atomic():
            page_index = 0
            for page_file_name in sorted([str(x) for x in cbx.namelist()], key=str.lower):
                try:
                    dot_index = page_file_name.rindex(".") + 1
                except ValueError:
                    continue
                ext = page_file_name.lower()[dot_index:]
                if ext in ["jpg", "jpeg"]:
                    content_type = "image/jpeg"
                elif ext == "png":
                    content_type = "image/png"
                elif ext == "bmp":
                    content_type = "image/bmp"
                elif ext == "gif":
                    content_type = "image/gif"
                else:
                    content_type = "text/plain"
                page = ComicPage(
                    Comic=book, index=page_index, page_file_name=page_file_name, content_type=content_type
                )
                page.save()
                page_index += 1

    @staticmethod
    def get_ordered_dir_list(folder):
        directories = []
        files = []
        for item in listdir(folder):
            if Path(folder, item).is_dir():
                directories.append(item)
            else:
                files.append(item)
        return sorted(directories) + sorted(files)


class ComicPage(models.Model):
    Comic = models.ForeignKey(ComicBook, on_delete=models.CASCADE)
    index = models.IntegerField()
    page_file_name = models.CharField(max_length=200, unique=False)
    content_type = models.CharField(max_length=30)


class ComicStatus(models.Model):
    user = models.ForeignKey(User, unique=False, null=False, on_delete=models.CASCADE)
    comic = models.ForeignKey(ComicBook, unique=False, null=False, on_delete=models.CASCADE)
    last_read_page = models.IntegerField(default=0)
    unread = models.BooleanField(default=True)
    finished = models.BooleanField(default=False)

    @property
    def read(self):
        return self.last_read_page

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"<ComicStatus:{self.user.username}:{self.comic.file_name}:{self.last_read_page}:"
            f"{self.unread}:{self.finished}"
        )


# TODO: add support to reference items last being read


class UserMisc(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    feed_id = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
