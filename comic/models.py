from django.db import models
from django.db.models import Max
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode



from unrar import rarfile
import zipfile
from os import path
import os


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
        out = (archive.open(page_obj.page_file_name), page_obj.content_type)
        return out

    def is_last_page(self, page):
        page_count = ComicPage.objects.filter(Comic=self).count()
        if (page_count - 1) == page:
            return True
        return False

    class Navigation:
        def __init__(self):
            self.next_index = 0
            self.next_path = ''
            self.prev_index = 0
            self.prev_path = ''
            self.cur_index = 0
            self.cur_path = ''
            self.q_prev_comic = False
            self.q_next_to_directory = False

    def nav(self, comic_path, page):
        out = self.Navigation()
        out.cur_index = page
        out.cur_path = comic_path

        if page == 0:
            out.prev_path, out.prev_index = self.nav_get_prev_comic(comic_path)
            if out.prev_index == -1:
                out.q_prev_to_directory = True
        else:
            out.prev_index = page - 1
            out.prev_path = comic_path

        if self.is_last_page(page):
            out.next_path, out.next_index = self.nav_get_next_comic(comic_path)
            if out.next_index == -1:
                out.q_next_to_directory = True
        else:
            out.next_index = page + 1
            out.next_path = comic_path

        return out
    def nav_get_prev_comic(self, comic_path):
        base_dir = Setting.objects.get(name='BASE_DIR').value
        comic_path = urlsafe_base64_decode(comic_path)
        directory, comic = path.split(comic_path)
        dir_list = os.listdir(path.join(base_dir, directory))
        comic_index = dir_list.index(comic)
        if comic_index == 0:
            comic_path = urlsafe_base64_encode(directory)
            index = -1
        else:
            prev_comic = dir_list[comic_index - 1]
            comic_path = path.join(directory, prev_comic)
            if not path.isdir(path.join(base_dir, prev_comic)):
                print path.join(base_dir, prev_comic)
                print path.join(base_dir, prev_comic)
                try:
                    book = ComicBook.objects.get(file_name=prev_comic)
                except ComicBook.DoesNotExist:
                    book = process_comic_book(base_dir, comic_path, prev_comic)
                index = ComicPage.objects.filter(Comic=book).count() - 1
                comic_path = urlsafe_base64_encode(comic_path)
            else:
                comic_path = urlsafe_base64_encode(directory)
                index = -1
        return comic_path, index
    def nav_get_next_comic(self, comic_path):
        base_dir = Setting.objects.get(name='BASE_DIR')
        comic_path = urlsafe_base64_decode(comic_path)
        directory, comic = path.split(comic_path)
        dir_list = os.listdir(path.join(base_dir.value, directory))
        comic_index = dir_list.index(comic)
        try:
            next_comic = dir_list[comic_index + 1]
            comic_path = path.join(directory, next_comic)
            comic_path = urlsafe_base64_encode(comic_path)
            index = 0
        except IndexError:
            comic_path = urlsafe_base64_encode(directory)
            index = -1
        return comic_path, index
    class Comic:
        def __init__(self):
            self.name = ''
            self.index = 0

    def pages(self):
        out = []
        for item in ComicPage.objects.filter(Comic=self).order_by('index'):
            i = self.Comic()
            i.name = item.page_file_name
            i.index = item.index
            out.append(i)
        return out
def process_comic_book(base_dir, comic_path, comic_file_name):
    try:
        cbx = rarfile.RarFile(path.join(base_dir, comic_path))
    except rarfile.BadRarFile:
        cbx = zipfile.ZipFile(path.join(base_dir, comic_path))
    except zipfile.BadZipfile:
        return False

    book = ComicBook(file_name=comic_file_name,
                     last_read_page=0)
    book.save()
    i = 0
    for f in sorted(cbx.namelist(), key=str.lower):
        ext = f.lower()[-3:]
        if ext in ['jpg', 'jpeg']:
            page = ComicPage(Comic=book,
                             index=i,
                             page_file_name=f,
                             content_type='image/jpeg')
            page.save()
            i += 1
        elif ext == 'png':
            page = ComicPage(Comic=book,
                             index=i,
                             page_file_name=f,
                             content_type='image/png')
            page.save()
            i += 1
        elif ext == 'bmp':
            page = ComicPage(Comic=book,
                             index=i,
                             page_file_name=f,
                             content_type='image/bmp')
            page.save()
            i += 1
        elif ext == 'gif':
            page = ComicPage(Comic=book,
                             index=i,
                             page_file_name=f,
                             content_type='image/gif')
            page.save()
            i += 1

    return book

class ComicPage(models.Model):
    Comic = models.ForeignKey(ComicBook)
    index = models.IntegerField()
    page_file_name = models.CharField(max_length=100, unique=False)
    content_type = models.CharField(max_length=30)



