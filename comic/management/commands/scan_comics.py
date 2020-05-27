import os
from os.path import isdir
from loguru import logger

from django.core.management.base import BaseCommand

from comic.models import ComicBook, Directory, Setting, ComicStatus


class Command(BaseCommand):
    help = "Scan directories to Update Comic DB"

    def __init__(self):
        super().__init__()
        self.base_dir = Setting.objects.get(name="BASE_DIR").value

    def add_arguments(self, parser):
        parser.add_argument(
            '--out',
            action='store_true',
            help='Output to console',
        )

    def handle(self, *args, **options):
        self.OUTPUT = True if options['out'] else False
        self.scan_directory()

    def scan_directory(self, directory=False):

        """

        :type directory: Directory
        """
        if not directory:
            comic_dir = self.base_dir
        else:
            comic_dir = os.path.join(self.base_dir, directory.path)
        if directory:
            books = ComicBook.objects.filter(directory=directory)
        else:
            books = ComicBook.objects.filter(directory__isnull=True)
        for book in books:
            if not os.path.isfile(os.path.join(comic_dir, book.file_name)):
                book.delete()
        for file in sorted(os.listdir(comic_dir)):
            if isdir(os.path.join(comic_dir, file)):
                if self.OUTPUT:
                    logger.info(f"Scanning Directory {file}")
                try:
                    if directory:
                        next_directory, created = Directory.objects.get_or_create(name=file, parent=directory)
                    else:
                        next_directory, created = Directory.objects.get_or_create(name=file, parent__isnull=True)
                except Directory.MultipleObjectsReturned:
                    if directory:
                        next_directories = Directory.objects.filter(name=file, parent=directory)
                    else:
                        next_directories = Directory.objects.filter(name=file, parent__isnull=True)
                    next_directories = next_directories.order_by('id')
                    next_directory = next_directories.first()
                    next_directories.exclude(id=next_directory.id).delete()
                    logger.error(f'Duplicate Directory {file}')
                    created = False
                if created:
                    next_directory.save()
                self.scan_directory(next_directory)
            else:
                if self.OUTPUT:
                    logger.info(f"Scanning File {file}")
                try:
                    if directory:
                        try:
                            book = ComicBook.objects.get(file_name=file, directory=directory)
                        except ComicBook.MultipleObjectsReturned:
                            logger.error(f'Duplicate Comic {file}')
                            books = ComicBook.objects.filter(file_name=file, directory=directory).order_by('id')
                            book = books.first()
                            extra_books = books.exclude(id=book.id)
                            extra_books.delete()
                        if book.version == 0:
                            book.version = 1
                            book.save()
                    else:
                        book = ComicBook.objects.get(file_name=file, directory__isnull=True)
                        if book.version == 0:
                            if directory:
                                book.directory = directory
                            book.version = 1
                            book.save()
                except ComicBook.DoesNotExist:
                    ComicBook.process_comic_book(file, directory)
