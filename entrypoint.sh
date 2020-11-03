wait-for-it.sh database:5432

python manage.py migrate --settings=cbreader.settings.base

python manage.py collectstatic --settings=cbreader.settings.base  --noinput

gunicorn --workers 3 --bind 0.0.0.0:8000 cbreader.wsgi:application