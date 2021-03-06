# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-13 15:28
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("comic", "0016_auto_20160414_1335")]

    operations = [
        migrations.CreateModel(
            name="UserMisc",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("feed_id", models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
        )
    ]
