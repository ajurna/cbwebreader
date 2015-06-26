# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comic', '0006_auto_20150625_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='name',
            field=models.CharField(unique=True, max_length=100),
        ),
    ]
