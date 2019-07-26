import os
from os.path import isdir

from django.core.management.base import BaseCommand

from comic.models import ComicBook, Directory, Setting


class Command(BaseCommand):
    help = "Scan directories to Update Comic DB"

    def __init__(self):
        super().__init__()
        self.base_dir = Setting.objects.get(name="BASE_DIR").value

    def handle(self, *args, **options):
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
        for file in os.listdir(comic_dir):
            if isdir(os.path.join(comic_dir, file)):
                if directory:
                    next_directory, created = Directory.objects.get_or_create(name=file, parent=directory)
                else:
                    next_directory, created = Directory.objects.get_or_create(name=file, parent__isnull=True)
                if created:
                    next_directory.save()
                self.scan_directory(next_directory)
            else:
                try:
                    if directory:
                        book = ComicBook.objects.get(file_name=file, directory=directory)
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
