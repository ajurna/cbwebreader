# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comic', '0002_auto_20150616_1613'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComicBook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_name', models.CharField(unique=True, max_length=100)),
                ('last_read_page', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ComicPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField()),
                ('page_file_name', models.CharField(max_length=100)),
                ('content_type', models.CharField(max_length=30)),
                ('Comic', models.ForeignKey(to='comic.ComicBook', on_delete=models.CASCADE)),
            ],
        ),
    ]
