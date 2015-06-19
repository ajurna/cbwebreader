from django.contrib import admin
from comic.models import Setting, ComicBook, ComicPage


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')


@admin.register(ComicBook)
class ComicBookAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'last_read_page')


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = ('Comic', 'index', 'page_file_name', 'content_type')
    list_filter = ['Comic']
