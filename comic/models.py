from django.db import models
from django.db.transaction import atomic
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.models import User

from comic import rarfile
from comic.util import get_ordered_dir_list
import zipfile
from os import path


class Setting(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    def __str__(self):
        return '"%s":"%s"' % (self.name, self.value)

    def __unicode__(self):
        return self.__str__()


class ComicBook(models.Model):
    file_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.file_name

    def get_image(self, archive_path, page):
        try:
            archive = rarfile.RarFile(archive_path)
        except rarfile.NotRarFile:
            archive = zipfile.ZipFile(archive_path)
        except zipfile.BadZipfile:
            return False
        page_obj = ComicPage.objects.get(Comic=self, index=page)
        out = (archive.open(page_obj.page_file_name), page_obj.content_type)
        return out

    def is_last_page(self, page):
        if (self.page_count - 1) == page:
            return True
        return False

    @property
    def page_count(self):
        page_count = ComicPage.objects.filter(Comic=self).count()
        return page_count

    class Navigation:
        def __init__(self):
            self.next_index = 0
            self.next_path = ''
            self.prev_index = 0
            self.prev_path = ''
            self.cur_index = 0
            self.cur_path = ''
            self.q_prev_to_directory = False
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

    @staticmethod
    def nav_get_prev_comic(comic_path):
        base_dir = Setting.objects.get(name='BASE_DIR').value
        comic_path = urlsafe_base64_decode(comic_path)
        directory, comic = path.split(comic_path)
        dir_list = get_ordered_dir_list(path.join(base_dir, directory))
        comic_index = dir_list.index(comic)
        if comic_index == 0:
            comic_path = urlsafe_base64_encode(directory)
            index = -1
        else:
            prev_comic = dir_list[comic_index - 1]
            comic_path = path.join(directory, prev_comic)
            if not path.isdir(path.join(base_dir, directory, prev_comic)):
                try:
                    book = ComicBook.objects.get(file_name=prev_comic)
                except ComicBook.DoesNotExist:
                    book = ComicBook.process_comic_book(base_dir, comic_path, prev_comic)
                index = ComicPage.objects.filter(Comic=book).count() - 1
                comic_path = urlsafe_base64_encode(comic_path)
            else:
                comic_path = urlsafe_base64_encode(directory)
                index = -1
        return comic_path, index

    @staticmethod
    def nav_get_next_comic(comic_path):
        base_dir = Setting.objects.get(name='BASE_DIR')
        comic_path = urlsafe_base64_decode(comic_path)
        directory, comic = path.split(comic_path)
        dir_list = get_ordered_dir_list(path.join(base_dir.value, directory))
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

    @staticmethod
    def process_comic_book(base_dir, comic_path, comic_file_name):
        try:
            cbx = rarfile.RarFile(path.join(base_dir, comic_path))
        except rarfile.NotRarFile:
            cbx = zipfile.ZipFile(path.join(base_dir, comic_path))
        except zipfile.BadZipfile:
            return False
        with atomic():
            book = ComicBook(file_name=comic_file_name)
            book.save()
            i = 0
            for f in sorted([str(x) for x in cbx.namelist()], key=str.lower):
                try:
                    dot_index = f.rindex('.') + 1
                except ValueError:
                    continue
                ext = f.lower()[dot_index:]
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

    class DirFile:
        def __init__(self):
            self.name = ''
            self.isdir = False
            self.icon = ''
            self.iscb = False
            self.location = ''
            self.label = ''
            self.cur_page = 0

        def __str__(self):
            return self.name

    @staticmethod
    def generate_directory(user, base_dir, comic_path):
        files = []
        for fn in get_ordered_dir_list(path.join(base_dir, comic_path)):
            df = ComicBook.DirFile()
            df.name = fn
            if path.isdir(path.join(base_dir, comic_path, fn)):
                df.isdir = True
                df.icon = 'glyphicon-folder-open'
                df.location = urlsafe_base64_encode(path.join(comic_path, fn))
            elif fn.lower()[-4:] in ['.rar', '.zip', '.cbr', '.cbz']:
                df.iscb = True
                df.icon = 'glyphicon-book'
                df.location = urlsafe_base64_encode(path.join(comic_path, fn))
                try:
                    book = ComicBook.objects.get(file_name=fn)
                    status, _ = ComicStatus.objects.get_or_create(comic=book, user=user)
                    last_page = status.last_read_page
                    if status.unread:
                        df.label = '<span class="label label-default pull-right">Unread</span>'
                    elif (last_page + 1) == book.page_count:
                        df.label = '<span class="label label-success pull-right">Read</span>'
                        df.cur_page = last_page
                    else:
                        label_text = '<span class="label label-primary pull-right">%s/%s</span>' % \
                                     (last_page + 1, book.page_count)
                        df.label = label_text
                        df.cur_page = last_page
                except ComicBook.DoesNotExist:
                    df.label = '<span class="label label-danger pull-right">Unprocessed</span>'
            files.append(df)
        return files

    @property
    def pages(self):
        out = []
        for item in ComicPage.objects.filter(Comic=self).order_by('index'):
            out.append(item)
        return out

    def page_name(self, index):
        return ComicPage.objects.get(Comic=self, index=index).page_file_name

class ComicPage(models.Model):
    Comic = models.ForeignKey(ComicBook)
    index = models.IntegerField()
    page_file_name = models.CharField(max_length=100, unique=False)
    content_type = models.CharField(max_length=30)

class ComicStatus(models.Model):
    user = models.ForeignKey(User, unique=False, null=False)
    comic = models.ForeignKey(ComicBook, unique=False, null=False)
    last_read_page = models.IntegerField(default=0)
    unread = models.BooleanField(default=True)
