# Generated by Django 4.0.7 on 2022-09-15 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comic', '0046_comicbook_one_comic_name_per_directory'),
    ]

    operations = [
        migrations.AddField(
            model_name='comicstatus',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
