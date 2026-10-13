"""Settings used by the test suite.

In-memory SQLite so the tests do not need a running Postgres, and a scratch comic
volume that the fixtures fill with generated archives.
"""

import os
from pathlib import Path

from cbreader.settings.base import *  # noqa: F403
from cbreader.settings.base import BASE_DIR

SECRET_KEY = 'test-secret-key'
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

COMIC_BOOK_VOLUME = Path(os.environ.get('COMIC_TEST_VOLUME', BASE_DIR / 'test_comics'))
MEDIA_ROOT = BASE_DIR / 'test_media'
