# Generated by Django 3.2.14 on 2022-07-07 16:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comic', '0030_auto_20220707_1720'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comicbook',
            name='directory',
        ),
    ]
