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
