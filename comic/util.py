from django.utils.http import urlsafe_base64_encode

from comic.models import ComicBook

from os import path
import os


class Breadcrumb:
    def __init__(self):
        self.name = 'Home'
        self.url = '/comic/'

    def __str__(self):
        return self.name

    def __unicode__(self):
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

def get_ordered_dir_list(folder):
    directories = []
    files = []
    print(folder)
    for item in os.listdir(folder):
        if path.isdir(path.join(folder, item)):
            directories.append(item)
        else:
            files.append(item)
    print(directories)
    return sorted(directories) + sorted(files)

def generate_directory(base_dir, comic_path):
    files = []
    for fn in get_ordered_dir_list(path.join(base_dir, comic_path)):
        df = DirFile()
        df.name = fn
        if path.isdir(path.join(base_dir, comic_path, fn)):
            df.isdir = True
            df.icon = 'glyphicon-folder-open'
            df.location = urlsafe_base64_encode(path.join(comic_path, fn))
        elif fn.lower().endswith('cbz') or fn.lower().endswith('cbr'):
            df.iscb = True
            df.icon = 'glyphicon-book'
            df.location = urlsafe_base64_encode(path.join(comic_path, fn))
            try:
                book = ComicBook.objects.get(file_name=fn)
                if book.unread:
                    df.label = '<span class="label label-default pull-right">Unread</span>'
                else:
                    last_page = book.last_read_page
                    label_text = '<span class="label label-primary pull-right">%s/%s</span>' % \
                                 (last_page, book.page_count)
                    df.label = label_text
                    df.cur_page = last_page
            except ComicBook.DoesNotExist:
                df.label = '<span class="label label-danger pull-right">Unprocessed</span>'
        files.append(df)
    return files
