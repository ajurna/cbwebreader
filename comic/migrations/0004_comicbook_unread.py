# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("comic", "0003_comicbook_comicpage")]

    operations = [
        migrations.AddField(
            model_name="comicbook", name="unread", field=models.BooleanField(default=True), preserve_default=False
        )
    ]
