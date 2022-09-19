import io
import mimetypes
import uuid
import zipfile
from functools import reduce
from pathlib import Path
from typing import Optional, List, Union, Tuple, Final, IO

# noinspection PyPackageRequirements
import fitz
import rarfile
from PIL import Image, UnidentifiedImageError
from PIL.Image import Image as Image_type
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import UniqueConstraint
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

    def __str__(self) -> str:
        return f"Directory: {self.name}; {self.parent}"

    @property
    def title(self) -> str:
        return self.name

    @property
    def type(self) -> str:
        return 'Directory'

    def generate_thumbnail(self) -> None:
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
            # pylint: disable=unnecessary-lambda
            return reduce(lambda x, y: Path(x, y), path_items)
        return Path(path_items[0])

    def get_path_items(self, path_items: Optional[List] = None) -> List[Path]:
        if path_items is None:
            path_items = []
        path_items.append(self.name)
        if self.parent:
            self.parent.get_path_items(path_items)
        return path_items

    def get_path_objects(self, path_items: Optional[List] = None) -> List["Directory"]:
        if path_items is None:
            path_items = []
        path_items.append(self)
        if self.parent:
            self.parent.get_path_objects(path_items)
        return path_items


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
    page_count = models.IntegerField(default=0)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['directory', 'file_name'], name='one_comic_name_per_directory')
        ]

    def __str__(self) -> str:
        return self.file_name

    @property
    def title(self) -> str:
        return self.file_name

    @property
    def type(self) -> str:
        return 'ComicBook'

    @property
    def total(self) -> int:
        return self.page_count

    def get_pdf(self) -> Path:
        base_dir = settings.COMIC_BOOK_VOLUME
        if self.directory:
            return Path(base_dir, self.directory.get_path(), self.file_name)
        return Path(base_dir, self.file_name)

    def get_image(self, page: int) -> Union[Tuple[IO[bytes], str], Tuple[bool, bool]]:
        base_dir = settings.COMIC_BOOK_VOLUME
        if self.directory:
            archive_path = Path(base_dir, self.directory.path, self.file_name)
        else:
            archive_path = Path(base_dir, self.file_name)
        try:
            archive = rarfile.RarFile(archive_path)
        except rarfile.NotRarFile:
            # pylint: disable=consider-using-with
            archive = zipfile.ZipFile(archive_path)
        except zipfile.BadZipfile:
            return False, False

        file_name, file_mime = self.get_archive_files(archive)[page]
        return archive.open(file_name), file_mime

    def generate_thumbnail_pdf(self, page_index: int = 0) -> Tuple[io.BytesIO, Image_type, str]:
        img, pil_data = self._get_pdf_image(page_index if page_index else 0)
        return img, pil_data, 'Image/JPEG'

    def generate_thumbnail_archive(self, page_index: int = 0) -> Union[Tuple[io.BytesIO, Image_type, str],
                                                                       Tuple[bool, bool, bool]]:
        img, content_type, pil_data = False, False, False
        if page_index:
            img, content_type = self.get_image(page_index)
            pil_data = Image.open(img)
        else:
            for page_number in range(self.page_count):
                try:
                    img, content_type = self.get_image(page_number)
                    pil_data = Image.open(img)
                    break
                except UnidentifiedImageError:
                    continue
        return img, pil_data, content_type

    def generate_thumbnail(self, page_index: int = None) -> None:

        if Path(self.file_name).suffix.lower() == '.pdf':
            img, pil_data, content_type = self.generate_thumbnail_pdf(page_index if page_index else 0)
        else:
            img, pil_data, content_type = self.generate_thumbnail_archive(page_index)
        if not img:
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

    def _get_pdf_image(self, page_index: int) -> Tuple[io.BytesIO, Image_type]:
        # noinspection PyUnresolvedReferences
        doc = fitz.open(self.get_pdf())
        page = doc[page_index]
        pix = page.get_pixmap()
        mode: Final = "RGBA" if pix.alpha else "RGB"
        # noinspection PyTypeChecker
        pil_data = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        img = io.BytesIO()
        pil_data.save(img, format="JPEG")
        img.seek(0)
        return img, pil_data

    @staticmethod
    def process_comic_book(comic_file_path: Path, directory: "Directory" = False) -> Union["ComicBook", Path]:
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
            book.page_count = len(book.get_archive_files(archive))
        elif archive_type == 'pdf':
            book.page_count = archive.page_count

        return book

    @property
    def get_archive_path(self) -> Path:
        if self.directory:
            return Path(settings.COMIC_BOOK_VOLUME, self.directory.get_path(), self.file_name)
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

    def get_page_count(self) -> int:
        archive, archive_type = self.get_archive()
        if archive_type == 'archive':
            return len(self.get_archive_files(archive))
        elif archive_type == 'pdf':
            return archive.page_count

    @staticmethod
    def get_archive_files(archive: Union[zipfile.ZipFile, rarfile.RarFile]) -> List[Tuple[str, str]]:
        return [
            (x, mimetypes.guess_type(x)[0]) for x in sorted(archive.namelist())
            if not x.endswith('/') and mimetypes.guess_type(x)[0] and not x.endswith('xml')
        ]


class ComicStatus(models.Model):
    user = models.ForeignKey(User, unique=False, null=False, on_delete=models.CASCADE)
    comic = models.ForeignKey(ComicBook, unique=False, blank=False, null=False, on_delete=models.CASCADE,
                              to_field="selector")
    last_read_page = models.IntegerField(default=0)
    unread = models.BooleanField(default=True)
    finished = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'comic'], name='one_per_user_per_comic')
        ]

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return (
            f"<ComicStatus:{self.user.username}:{self.comic.file_name}:{self.last_read_page}:"
            f"{self.unread}:{self.finished}"
        )


class UserMisc(models.Model):

    user = AutoOneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    feed_id = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    allowed_to_read = models.PositiveSmallIntegerField(default=Directory.Classification.C_18,
                                                       choices=Directory.Classification.choices)
