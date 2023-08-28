from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.management.base import BaseCommand, CommandParser
from loguru import logger

from comic.models import Directory
from comic.processing import generate_directory


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

    def scan_directory(self, user: Optional[AbstractBaseUser] = None, directory: Optional[Directory] = None) -> None:
        if not user:
            user_model = get_user_model()
            user: AbstractBaseUser = user_model.objects.first()
        for item in generate_directory(user, directory):
            if item is Directory:
                logger.info(item)
                self.scan_directory(user, item)
