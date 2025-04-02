from .base import INSTALLED_APPS, MIDDLEWARE, SILK_ENABLED

INSTALLED_APPS += ["silk"]

MIDDLEWARE += [
    'silk.middleware.SilkyMiddleware',
]

SILK_ENABLED = True  # noqa: F811

SILKY_PYTHON_PROFILER = True
