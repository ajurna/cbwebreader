from django.contrib import admin

from comic.models import ComicBook, ComicPage, ComicStatus, Directory


@admin.register(ComicBook)
class ComicBookAdmin(admin.ModelAdmin):
    list_display = ["file_name", "date_added"]
    search_fields = ["file_name"]


@admin.register(ComicPage)
class ComicPageAdmin(admin.ModelAdmin):
    list_display = ("Comic", "index", "page_file_name", "content_type")
    list_filter = ["Comic"]


@admin.register(ComicStatus)
class ComicStatusAdmin(admin.ModelAdmin):
    list_display = ["user", "comic", "last_read_page", "unread"]


@admin.register(Directory)
class DirectoryAdmin(admin.ModelAdmin):
    pass
