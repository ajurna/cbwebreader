# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Directory, ComicBook, ComicPage, ComicStatus, UserMisc


@admin.register(Directory)
class DirectoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent', 'selector')
    raw_id_fields = ('parent',)
    search_fields = ('name',)


@admin.register(ComicBook)
class ComicBookAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'file_name',
        'date_added',
        'directory',
        'selector',
        'version',
    )
    list_filter = ('date_added',)
    raw_id_fields = ('directory',)


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'Comic', 'index', 'page_file_name', 'content_type')
    raw_id_fields = ('Comic',)


@admin.register(ComicStatus)
class ComicStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'comic',
        'last_read_page',
        'unread',
        'finished',
    )
    list_filter = ('unread', 'finished')
    raw_id_fields = ('user', 'comic')


@admin.register(UserMisc)
class UserMiscAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'feed_id')
    list_filter = ('user',)