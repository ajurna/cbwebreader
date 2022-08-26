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
from django.db.models import UniqueConstraint
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
    parent = models.ForeignKey("Directory", null=True, blank=True, on_delete=models.CASCADE, to_field="selector")
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

    @property
    def title(self):
        return self.name

    @property
    def type(self):
        return 'Directory'

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


class ComicBook(models.Model):
    file_name = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    directory = models.ForeignKey(Directory, blank=True, null=True, on_delete=models.CASCADE, to_field="selector")
    selector = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    version = models.IntegerField(default=1)
    thumbnail = ProcessedImageField(upload_to='thumbs',
                                    processors=[ResizeToFill(200, 300)],
                                    format='JPEG',
                                    options={'quality': 60},
                                    null=True)
    thumbnail_index = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['directory', 'file_name'], name='one_comic_name_per_directory')
        ]

    def __str__(self):
        return self.file_name

    @property
    def title(self):
        return self.file_name

    @property
    def type(self):
        return 'ComicBook'

    def get_pdf(self) -> Path:
        base_dir = settings.COMIC_BOOK_VOLUME
        if self.directory:
            return Path(base_dir, self.directory.get_path(), self.file_name)
        else:
            return Path(base_dir, self.file_name)

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
            self.verify_pages()
            page_obj = ComicPage.objects.get(Comic=self, index=page)
            out = (archive.open(page_obj.page_file_name), page_obj.content_type)
        return out

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

    @property
    def page_count(self):
        return ComicPage.objects.filter(Comic=self).count()

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
    comic = models.ForeignKey(ComicBook, unique=False, blank=False, null=False, on_delete=models.CASCADE, to_field="selector")
    last_read_page = models.IntegerField(default=0)
    unread = models.BooleanField(default=True)
    finished = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'comic'], name='one_per_user_per_comic')
        ]

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
