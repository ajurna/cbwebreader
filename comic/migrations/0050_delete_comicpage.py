# Generated by Django 4.0.7 on 2022-09-15 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comic', '0049_populate_pages'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ComicPage',
        ),
    ]
