"""
Django settings for cbreader project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from datetime import timedelta
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.parent

load_dotenv(override=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', False) == 'True'

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'drf_yasg',
    'webpack_loader',
    "comic",
    'django_extensions',
    'imagekit',
    'django_boost',
    "corsheaders",
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    # 'silk'
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = "cbreader.urls"


WSGI_APPLICATION = "cbreader.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_URL = os.getenv("DATABASE_URL")

# docker-compose passes DB_* variables, not a URL. Without building one from them the
# app silently falls back to sqlite inside the container, and the web and cron
# containers end up with two separate databases.
if not DATABASE_URL and os.getenv("DB_HOST"):
    DATABASE_URL = "postgres://{}:{}@{}/{}".format(
        quote(os.getenv("DB_USER", "postgres"), safe=""),
        quote(os.getenv("DB_PASS", ""), safe=""),
        os.getenv("DB_HOST"),
        os.getenv("DB_DATABASE", "postgres"),
    )

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=500)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "db.sqlite3")}}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-ie"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    Path(BASE_DIR, "static"),
    Path(BASE_DIR, "frontend", "dist")
]

STATIC_ROOT = os.getenv('STATIC_ROOT', None)


MEDIA_ROOT = os.getenv('MEDIA_ROOT', None)

MEDIA_URL = '/media/'

UNRAR_TOOL = os.getenv("DJANGO_UNRAR_TOOL", None)


COMIC_BOOK_VOLUME = Path(os.getenv("COMIC_BOOK_VOLUME", '/comics'))

if DEBUG:
    min_level = 'DEBUG'
else:
    min_level = 'INFO'

min_django_level = 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # keep Django's default loggers
    'formatters': {
        # see full list of attributes here:
        # https://docs.python.org/3/library/logging.html#logrecord-attributes
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'timestampthread': {
            'format': "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(name)-20.20s]  %(message)s",
        },
    },
    'handlers': {
        'logfile': {
            # optionally raise to INFO to not fill the log file too quickly
            'level': min_level,  # this level or higher goes to the log file
            'class': 'logging.handlers.RotatingFileHandler',
            # IMPORTANT: replace with your desired logfile name!
            'filename': os.path.join(BASE_DIR, 'djangoproject.log'),
            'maxBytes': 50 * 10**6,  # will 50 MB do?
            'backupCount': 3,  # keep this many extra historical files
            'formatter': 'timestampthread'
        },
        'console': {
            'level': min_level,  # this level or higher goes to the console
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {  # configure all of Django's loggers
            'handlers': ['logfile', 'console'],
            'level': min_django_level,  # this level or higher goes to the console
            'propagate': False,  # don't propagate further, to avoid duplication
        },
        # root configuration – for all of our own apps
        # (feel free to do separate treatment for e.g. brokenapp vs. sth else)
        '': {
            'handlers': ['logfile', 'console'],
            'level': min_level,  # this level or higher goes to the console,
        },
    },
}

USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', False) == 'True'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CSP_DEFAULT_SRC = ("'none'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'"
)
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-eval'", "'unsafe-inline'", "localhost:8001")
CSP_CONNECT_SRC = ("'self'", "ws://localhost:8001/ws")
CSP_INCLUDE_NONCE_IN = ['script-src']
CSP_SCRIPT_SRC_ATTR = ("'self'",)  # "'unsafe-inline'")


PERMISSIONS_POLICY: Dict[str, List] = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
}


REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'comic.auth.CookieJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

CORS_ALLOW_ALL_ORIGINS = True
# Cookie based JWT authentication (see comic/auth.py). Tokens are stored in HttpOnly
# cookies so that browser initiated requests, such as the page images in the reader,
# can be authenticated - an <img> tag cannot send an Authorization header.
JWT_ACCESS_COOKIE_NAME = os.getenv('JWT_ACCESS_COOKIE_NAME', 'access_token')
JWT_REFRESH_COOKIE_NAME = os.getenv('JWT_REFRESH_COOKIE_NAME', 'refresh_token')
JWT_COOKIE_PATH = os.getenv('JWT_COOKIE_PATH', '/')
# Only mark the cookies Secure when the site is actually served over HTTPS, otherwise
# browsers drop them on plain http.
JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', 'False') == 'True'
# Lax blocks cross-site POSTs, which is the CSRF protection for cookie authentication.
JWT_COOKIE_SAMESITE = os.getenv('JWT_COOKIE_SAMESITE', 'Lax')

def lifetime_from_env(name: str, unit: str, default: int) -> timedelta:
    """Read a number of `unit` from the environment, falling back to `default`."""
    try:
        return timedelta(**{unit: int(os.getenv(name))})
    except (TypeError, ValueError):
        return timedelta(**{unit: default})


# The access token stays short so a session that should end ends quickly: a reader who
# closes the tab is logged out within minutes of their last page. The refresh token is
# the session - it is exchanged once (ROTATE_REFRESH_TOKENS plus BLACKLIST_AFTER_ROTATION
# below), and its window is how long a reader may be away before signing in again.
# Override with JWT_ACCESS_MINUTES / JWT_REFRESH_DAYS (see .env.example).
SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    'ACCESS_TOKEN_LIFETIME': lifetime_from_env('JWT_ACCESS_MINUTES', 'minutes', 10),
    'REFRESH_TOKEN_LIFETIME': lifetime_from_env('JWT_REFRESH_DAYS', 'days', 30),
    'LEEWAY': timedelta(seconds=30),
    'ALGORITHM': 'HS256',
    'AUDIENCE': 'cbwebreader-users',
    'ISSUER': 'cbwebreader',
}

# Renderer formats no longer include a leading dot, so the URL pattern in
# cbreader/urls.py matches the dot separately. See cbreader/urls.py.
SWAGGER_USE_COMPAT_RENDERERS = False

# Folder scans run through comic.tasks.scan_directory. The immediate backend runs the task
# in the caller, which is enough today; swapping to a queue backend later changes only
# this block, not the call sites.
TASKS = {
    'default': {
        'BACKEND': os.getenv('TASK_BACKEND', 'django.tasks.backends.immediate.ImmediateBackend'),
    },
}

FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': '/bundles/',  # must end with slash
        'STATS_FILE': os.path.join(FRONTEND_DIR, 'webpack-stats.json'),
        'INTEGRITY': not DEBUG,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

SUPPORTED_FILES = [".rar", ".zip", ".cbr", ".cbz", ".pdf"]
