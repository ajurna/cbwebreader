from django.utils.http import urlsafe_base64_encode
from comic.models import ComicBook, ComicPage
from unrar import rarfile
import zipfile
from os import path
import os


class Breadcrumb:
    def __init__(self):
        self.name = 'Home'
        self.url = '/comic/'

    def __str__(self):
        return self.name


class DirFile:
    def __init__(self):
        self.name = ''
        self.isdir = False
        self.icon = ''
        self.iscb = False
        self.location = ''

    def __str__(self):
        return self.name



def process_comic_book(base_dir, comic_path, comic_file_name):
    try:
        cbx = rarfile.RarFile(path.join(base_dir.value, comic_path))
    except rarfile.BadRarFile:
        cbx = zipfile.ZipFile(path.join(base_dir.value, comic_path))
    except zipfile.BadZipfile:
        return False

    book = ComicBook(file_name=comic_file_name,
                     last_read_page=0)
    book.save()
    i = 0
    for f in cbx.namelist():
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


def generate_breadcrumbs(comic_path):
    output = [Breadcrumb()]
    prefix = '/comic/'
    last = ''
    comic_path = path.normpath(comic_path)
    folders = comic_path.split(os.sep)
    for item in folders:
        if item == '.':
            continue
        bc = Breadcrumb()
        bc.name = item
        last = path.join(last, item)
        bc.url = prefix + urlsafe_base64_encode(last)
        output.append(bc)
    return output


def generate_directory(base_dir, comic_path):
    files = []
    for fn in os.listdir(path.join(base_dir.value, comic_path)):
        df = DirFile()
        df.name = fn
        if path.isdir(path.join(base_dir.value, comic_path, fn)):
            df.isdir = True
            df.icon = 'glyphicon-folder-open'
            df.location = urlsafe_base64_encode(path.join(comic_path, fn))
        elif fn.lower().endswith('cbz') or fn.lower().endswith('cbr'):
            df.iscb = True
            df.icon = 'glyphicon-book'
            df.location = urlsafe_base64_encode(path.join(comic_path, fn))
        files.append(df)
    return files
