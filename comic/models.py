import io
import mimetypes
import uuid
import zipfile
from functools import reduce
from itertools import zip_longest, chain
from pathlib import Path
from typing import Optional, List, Union, Tuple

import fitz
import rarfile
from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.transaction import atomic
from django.templatetags.static import static
from django.utils.http import urlsafe_base64_encode
from django_boost.models.fields import AutoOneToOneField
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

from comic.errors import NotCompatibleArchive

if settings.UNRAR_TOOL:
    rarfile.UNRAR_TOOL = settings.UNRAR_TOOL


class Directory(models.Model):
    class Classification(models.IntegerChoices):
        C_G = 0, 'G'
        C_PG = 1, 'PG'
        C_12 = 2, '12'
        C_15 = 3, '15'
        C_18 = 4, '18'

    name = models.CharField(max_length=100)
    parent = models.ForeignKey("Directory", null=True, blank=True, on_delete=models.CASCADE)
    selector = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    thumbnail = ProcessedImageField(upload_to='thumbs',
                                    processors=[ResizeToFill(200, 300)],
                                    format='JPEG',
                                    options={'quality': 60},
                                    null=True)
    thumbnail_issue = models.ForeignKey("ComicBook", null=True,
                                        on_delete=models.SET_NULL,
                                        related_name='directory_thumbnail_issue')
    thumbnail_index = models.PositiveIntegerField(default=0)
    classification = models.PositiveSmallIntegerField(choices=Classification.choices, default=Classification.C_18)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "Directory: {0}; {1}".format(self.name, self.parent)

    def mark_read(self, user):
        books = ComicBook.objects.filter(directory=self)
        for book in books:
            book.mark_read(user)

    def mark_unread(self, user):
        books = ComicBook.objects.filter(directory=self)
        for book in books:
            book.mark_unread(user)

    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            self.generate_thumbnail()
            if self.thumbnail:
                return self.thumbnail.url
            else:
                return static('img/placeholder.png')

    def generate_thumbnail(self):
        book: ComicBook = ComicBook.objects.filter(directory=self).order_by('file_name').first()
        if not book:
            return
        if not book.thumbnail:
            book.generate_thumbnail()
        self.thumbnail = book.thumbnail
        self.save()

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

    @property
    def url_safe_selector(self):
        return urlsafe_base64_encode(self.selector.bytes)

    def set_classification(self, form_data):
        self.classification = form_data['classification']
        self.save()


class ComicBook(models.Model):
    file_name = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    directory = models.ForeignKey(Directory, blank=True, null=True, on_delete=models.CASCADE)
    selector = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    version = models.IntegerField(default=1)
    thumbnail = ProcessedImageField(upload_to='thumbs',
                                    processors=[ResizeToFill(200, 300)],
                                    format='JPEG',
                                    options={'quality': 60},
                                    null=True)
    thumbnail_index = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.file_name

    def mark_read(self, user: User):
        status, _ = ComicStatus.objects.get_or_create(comic=self, user=user)
        status.mark_read()

    def mark_unread(self, user: User):
        status, _ = ComicStatus.objects.get_or_create(comic=self, user=user)
        status.mark_unread()

    def mark_previous(self, user):
        books = ComicBook.objects.filter(directory=self.directory).order_by('file_name')
        for book in books:
            if book == self:
                break
            book.mark_read(user)

    @property
    def url_safe_selector(self):
        return urlsafe_base64_encode(self.selector.bytes)

    def get_pdf(self) -> Path:
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
        out = (archive.open(page_obj.page_file_name), page_obj.content_type)
        return out

    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            self.generate_thumbnail()
            return self.thumbnail.url

    def generate_thumbnail(self, page_index: int = None):

        if Path(self.file_name).suffix.lower() == '.pdf':
            if page_index:
                img, pil_data = self._get_pdf_image(page_index)
            else:
                img, pil_data = self._get_pdf_image(0)
            content_type = 'Image/JPEG'
        else:
            if page_index:
                img, content_type = self.get_image(page_index)
                pil_data = Image.open(img)
            else:
                for x in range(ComicPage.objects.filter(Comic=self).count()):
                    try:
                        img, content_type = self.get_image(x)
                        pil_data = Image.open(img)
                        break
                    except UnidentifiedImageError:
                        continue
                try:
                    img
                    content_type
                    pil_data
                except NameError:
                    return
        self.thumbnail = InMemoryUploadedFile(
            img,
            None,
            f'{self.file_name}.jpg',
            content_type,
            pil_data.tell(),
            None
        )
        self.save()

    def _get_pdf_image(self, page_index: int):
        # noinspection PyTypeChecker
        doc = fitz.open(self.get_pdf())
        page = doc[page_index]
        pix = page.get_pixmap()
        mode = "RGBA" if pix.alpha else "RGB"
        pil_data = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        img = io.BytesIO()
        pil_data.save(img, format="JPEG")
        img.seek(0)
        return img, pil_data

    def is_last_page(self, page):
        if (self.page_count - 1) == page:
            return True
        return False

    @property
    def page_count(self):
        return ComicPage.objects.filter(Comic=self).count()

    def nav(self, user):
        next_path, next_type = self.nav_get_next_comic(user)
        prev_path, prev_type = self.nav_get_prev_comic(user)
        return {
            "next_path": next_path,
            "next_type": next_type,
            "prev_path": prev_path,
            "prev_type": prev_type,
            "cur_path": urlsafe_base64_encode(self.selector.bytes)
        }

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
                comic_path = urlsafe_base64_encode(self.directory.selector.bytes), type(self.directory).__name__
            else:
                comic_path = "", None
        else:
            prev_comic = dir_list[comic_index - 1]

            if Path(folder, prev_comic).is_dir():
                if self.directory:
                    comic_path = urlsafe_base64_encode(self.directory.selector.bytes), type(self.directory).__name__
                else:
                    comic_path = "", None
            else:
                try:
                    if self.directory:
                        book = ComicBook.objects.get(file_name=prev_comic, directory=self.directory)
                    else:
                        book = ComicBook.objects.get(file_name=prev_comic, directory__isnull=True)
                except ComicBook.DoesNotExist:
                    if self.directory:
                        book = ComicBook.process_comic_book(Path(prev_comic), self.directory)
                    else:
                        book = ComicBook.process_comic_book(Path(prev_comic))
                cs, _ = ComicStatus.objects.get_or_create(comic=book, user=user)
                comic_path = urlsafe_base64_encode(book.selector.bytes), type(book).__name__

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
                    book = ComicBook.process_comic_book(Path(next_comic), self.directory)
                else:
                    book = ComicBook.process_comic_book(Path(next_comic))
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
            comic_path = urlsafe_base64_encode(book.selector.bytes), type(book).__name__
        except IndexError:
            if self.directory:
                comic_path = urlsafe_base64_encode(self.directory.selector.bytes), type(self.directory).__name__
            else:
                comic_path = "", None
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

    @staticmethod
    def process_comic_book(comic_file_path: Path, directory: "Directory" = False) -> Union["ComicBook", Path]:
        """

        :type comic_file_path: str
        :type directory: Directory
        """
        try:
            book = ComicBook.objects.get(file_name=comic_file_path.name, version=0)
            book.directory = directory
            book.version = 1
            book.save()
            return book
        except ComicBook.DoesNotExist:
            pass

        book = ComicBook(file_name=comic_file_path.name, directory=directory if directory else None)
        book.save()
        try:
            archive, archive_type = book.get_archive()
        except NotCompatibleArchive:
            return comic_file_path

        if archive_type == 'archive':
            book.verify_pages()
        elif archive_type == 'pdf':
            with atomic():
                for page_index in range(archive.page_count):
                    page = ComicPage(
                        Comic=book, index=page_index, page_file_name=page_index + 1, content_type='application/pdf'
                    )
                    page.save()
        return book

    @staticmethod
    def get_ordered_dir_list(folder: Path) -> List[str]:
        directories = []
        files = []
        for item in folder.glob('*'):
            if item.is_dir():
                directories.append(item)
            else:
                files.append(item)
        return [x.name for x in chain(sorted(directories), sorted(files))]

    @property
    def get_archive_path(self):
        if self.directory:
            return Path(settings.COMIC_BOOK_VOLUME, self.directory.get_path(), self.file_name)
        else:
            return Path(settings.COMIC_BOOK_VOLUME, self.file_name)

    def get_archive(self) -> Tuple[Union[rarfile.RarFile, zipfile.ZipFile, fitz.Document], str]:
        archive_path = self.get_archive_path
        try:
            return rarfile.RarFile(archive_path), 'archive'
        except rarfile.NotRarFile:
            pass
        try:
            return zipfile.ZipFile(archive_path), 'archive'
        except zipfile.BadZipFile:
            pass

        try:
            # noinspection PyUnresolvedReferences
            return fitz.open(str(archive_path)), 'pdf'
        except RuntimeError:
            pass
        raise NotCompatibleArchive

    @staticmethod
    def get_archive_files(archive):
        return [
            (x, mimetypes.guess_type(x)[0]) for x in sorted(archive.namelist())
            if not x.endswith('/') and mimetypes.guess_type(x)[0]
        ]

    def verify_pages(self, pages: Optional["ComicPage"] = None):
        if not pages:
            pages = ComicPage.objects.filter(Comic=self)

        archive, archive_type = self.get_archive()
        if archive_type == 'pdf':
            return
        archive_files = self.get_archive_files(archive)
        index = 0
        for a_file, db_file in zip_longest(archive_files, pages):
            if not a_file:
                db_file.delete()
                continue
            if not db_file:
                ComicPage(
                    Comic=self,
                    page_file_name=a_file[0],
                    index=index,
                    content_type=a_file[1]
                ).save()
                index += 1
                continue
            changed = False
            if a_file[0] != db_file.page_file_name:
                db_file.page_file_name = a_file[0]
                changed = True
            if a_file[1] != db_file.content_type:
                db_file.content_type = a_file[1]
                changed = True
            if changed:
                db_file.save()
            index += 1


class ComicPage(models.Model):
    Comic = models.ForeignKey(ComicBook, on_delete=models.CASCADE)
    index = models.IntegerField()
    page_file_name = models.CharField(max_length=200, unique=False)
    content_type = models.CharField(max_length=30)

    class Meta:
        ordering = ['index']


class ComicStatus(models.Model):
    user = models.ForeignKey(User, unique=False, null=False, on_delete=models.CASCADE)
    comic = models.ForeignKey(ComicBook, unique=False, null=False, on_delete=models.CASCADE)
    last_read_page = models.IntegerField(default=0)
    unread = models.BooleanField(default=True)
    finished = models.BooleanField(default=False)

    def mark_read(self):
        page_count = ComicPage.objects.filter(Comic=self.comic).count()
        self.unread = False
        self.finished = True
        self.last_read_page = page_count - 1
        self.save()

    def mark_unread(self):
        self.unread = True
        self.finished = False
        self.last_read_page = 0
        self.save()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            f"<ComicStatus:{self.user.username}:{self.comic.file_name}:{self.last_read_page}:"
            f"{self.unread}:{self.finished}"
        )


# TODO: add support to reference items last being read


class UserMisc(models.Model):

    user = AutoOneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    feed_id = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    allowed_to_read = models.PositiveSmallIntegerField(default=Directory.Classification.C_18,
                                                       choices=Directory.Classification.choices)
