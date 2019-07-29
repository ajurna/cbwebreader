# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("comic", "0005_auto_20150625_1400")]

    operations = [
        migrations.AlterField(model_name="comicstatus", name="last_read_page", field=models.IntegerField(default=0)),
        migrations.AlterField(model_name="comicstatus", name="unread", field=models.BooleanField(default=True)),
    ]
