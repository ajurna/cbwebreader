# cbwebreader
Web Based CBR and CBZ file reader.
This is for if you have a collection of comics on a media server and want to read them remotely.

# Requirments

- [Django 1.9](https://www.djangoproject.com/)
- [python 3.5](https://www.python.org/)
- [rarfile python library by Marko Kreen](https://github.com/markokr/rarfile) (included)
- [Unrar by winrar](http://rarlabs.com)
- [django-recaptcha by praekelt](https://github.com/praekelt/django-recaptcha)

# Installation
Pull from git and use like any django project.

Also has a task manage.py scan_comics.
Use this after getting setup and it will speed up your browsing.
to keep your comics always up to date you should set this up as a scheduled task to run
as often as you wish, that way the recent comics page will work best.


# License
https://creativecommons.org/licenses/by-sa/4.0/
