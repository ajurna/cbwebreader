# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-14 12:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("comic", "0015_auto_20160405_1126")]

    operations = [
        migrations.AlterField(model_name="comicpage", name="page_file_name", field=models.CharField(max_length=200))
    ]