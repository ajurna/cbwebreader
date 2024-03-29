# Generated by Django 4.0.7 on 2022-09-15 09:59

from django.db import migrations
from django.db.models import Count


def forwards_func(apps, schema_editor):
    books = apps.get_model("comic", "ComicBook")
    for book in books.objects.all().annotate(total_pages=Count('comicpage')):
        book.page_count = book.total_pages
        book.save()


class Migration(migrations.Migration):

    dependencies = [
        ('comic', '0048_comicbook_page_count'),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
