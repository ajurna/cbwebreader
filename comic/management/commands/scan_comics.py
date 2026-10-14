from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from loguru import logger

from comic.models import ComicBook, Directory
from comic.processing import reconcile


class Command(BaseCommand):
    help = "Scan directories to Update Comic DB"

    def __init__(self) -> None:
        super().__init__()
        self.OUTPUT = False

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--out',
            action='store_true',
            help='Output to console',
        )
        parser.add_argument(
            '--if-empty',
            action='store_true',
            help='Do nothing when the database already contains books, so it is safe to run on startup.',
        )

    def handle(self, *args, **options) -> None:
        self.OUTPUT = options.get('out', False)
        if options.get('if_empty') and ComicBook.objects.exists():
            logger.info('The database already contains books, so the startup scan is skipped.')
            return
        self.scan_directory()

    def scan_directory(self, directory: Directory | None = None) -> None:
        reconcile(directory)
        path = Path(settings.COMIC_BOOK_VOLUME, directory.path) if directory else settings.COMIC_BOOK_VOLUME
        if self.OUTPUT:
            self.stdout.write(str(path))
        else:
            logger.info(path)
        for child in Directory.objects.filter(parent=directory):
            self.scan_directory(child)
