#!/usr/bin/env sh
set -e

python manage.py migrate --settings=cbreader.settings.base

# Index the library on the first run so the UI is not empty until cron gets to it.
# --if-empty makes this a no-op on every later start.
python manage.py scan_comics --if-empty --settings=cbreader.settings.base

python manage.py collectstatic --settings=cbreader.settings.base --noinput --clear

exec gunicorn --workers 3 --bind 0.0.0.0:8000 cbreader.wsgi:application
