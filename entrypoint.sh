#!/usr/bin/env sh
uv run manage.py migrate --settings=cbreader.settings.base

uv run manage.py collectstatic --settings=cbreader.settings.base  --noinput --clear

uv run gunicorn --workers 3 --bind 0.0.0.0:8000 cbreader.wsgi:application
