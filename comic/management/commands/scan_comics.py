from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from loguru import logger

from comic.models import Directory
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

    def handle(self, *args, **options) -> None:
        self.OUTPUT = options.get('out', False)
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
