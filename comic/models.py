from django.db import models
from unrar import rarfile
import zipfile
# Create your models here.

class Setting(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.TextField()

    def __str__(self):
        return '"%s":"%s"' % (self.name, self.value)

    def __unicode__(self):
        return self.__str__()

class ComicBook(models.Model):
    file_name = models.CharField(max_length=100, unique=True)
    last_read_page = models.IntegerField()

    class Comic:
        def __init__(self):
            self.name = ''
            self.index = 0
    class Navigation:
        def __init__(self):
            self.next_index = 0
            self.next_path = ''
            self.prev_index = 0
            self.prev_path = ''
            self.cur_index = 0
            self.cur_path = ''
    def __str__(self):
        return self.file_name
    def get_image(self, archive_path, page):
        try:
            archive = rarfile.RarFile(archive_path)
        except rarfile.BadRarFile:
            archive = zipfile.ZipFile(archive_path)
        except zipfile.BadZipfile:
            return False
        page_obj = ComicPage.objects.get(Comic=self, index=page)

        return (archive.open(page_obj.page_file_name), page_obj.content_type)

    def nav(self, comic_path, page):
        out = self.Navigation()
        out.cur_index = page
        out.cur_path = comic_path
        out.prev_index = page - 1
        out.next_index = page + 1
        out.prev_path = comic_path
        out.next_path = comic_path
        return out
    def pages(self):
        out = []
        for item in ComicPage.objects.filter(Comic=self).order_by('index'):
            i = self.Comic()
            i.name = item.page_file_name
            i.index = item.index
            out.append(i)
        return out
class ComicPage(models.Model):
    Comic = models.ForeignKey(ComicBook)
    index = models.IntegerField()
    page_file_name = models.CharField(max_length=100, unique=False)
    content_type = models.CharField(max_length=30)
