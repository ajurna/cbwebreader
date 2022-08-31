"""
Django settings for cbreader project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from datetime import timedelta
from pathlib import Path

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

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'drf_yasg',
    'webpack_loader',
    'bootstrap4',
    "comic",
    'django_extensions',
    'imagekit',
    'django_boost',
    'sri',
    "corsheaders",
    'django_filters',
    'rest_framework',
    # 'silk'
)

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
    # 'silk.middleware.SilkyMiddleware',
    # 'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = "cbreader.urls"


WSGI_APPLICATION = "cbreader.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {"default": dj_database_url.config(conn_max_age=500)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "db.sqlite3")}}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-ie"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

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

LOGIN_REDIRECT_URL = "/comic/"

LOGIN_URL = "/login/"

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

SILK_ENABLED = False

USE_X_FORWARDED_HOST = os.getenv('USE_X_FORWARDED_HOST', False) == 'True'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

MYLAR_API_KEY = os.getenv('MYLAR_API_KEY', None)

BOOTSTRAP4 = {
    "javascript_url": {
        "url": "https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js",
        "integrity": "sha384-Piv4xVNRyMGpqkS2by6br4gNJ7DXjqk09RmUpJ8jgGtD7zP9yug3goQfGII0yAns",
        "crossorigin": "anonymous",
    },
}
CSP_DEFAULT_SRC = ("'none'",)
CSP_STYLE_SRC = ("'self'", "'sha256-MBVp6JYxbC/wICelYC6eULCRpgi9kGezXXSaq/TS2+I='")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_INCLUDE_NONCE_IN = ['script-src']
CSP_SCRIPT_SRC_ATTR = ("'self'",)# "'unsafe-inline'")


PERMISSIONS_POLICY = {
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
        'rest_framework.authentication.SessionAuthentication',
    )
}

CORS_ALLOW_ALL_ORIGINS = True
SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
    'LEEWAY': timedelta(minutes=5),
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
