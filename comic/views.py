from django.http import HttpResponse
from django.template import RequestContext, loader
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from comic.models import Setting

from unrar import rarfile
from zipfile import ZipFile
import os
from os import path

class Comic:
    def __init__(self):
        self.name = ''
        self.index = 0
class Navigation:
    def __init__(self):
        self.next = 0
        self.prev = 0
        self.cur = 0
class DirFile:
    def __init__(self):
        self.name = ''
        self.isdir = False
        self.icon = ''
        self.iscb = False
        self.location = ''

    def __str__(self):
        return self.name


# Create your views here.
def index(request, comic_path=''):
    base_dir = Setting.objects.get(name='BASE_DIR')
    comic_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs(comic_path)


    #list and classify files
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
    template = loader.get_template('comic/index.html')
    context = RequestContext(request, {
        'file_list': files,
        'breadcrumbs': breadcrumbs,
    })
    return HttpResponse(template.render(context))


def read_comic(request, comic_path, page):
    encoded = comic_path
    comic_path = urlsafe_base64_decode(comic_path)
    base_dir = Setting.objects.get(name='BASE_DIR')
    template = loader.get_template('comic/read_comic.html')
    if comic_path.lower().endswith('cbr'):
        cbx = rarfile.RarFile(path.join(base_dir.value, comic_path))
    elif comic_path.lower().endswith('cbz'):
        cbx = ZipFile(path.join(base_dir.value, comic_path))
    nav = Navigation()
    page = int(page)
    nav.cur = page
    nav.next = page + 1
    nav.prev = page - 1
    pages = []
    for idx, name in enumerate(cbx.namelist()):
        comic = Comic()
        comic.name = name
        comic.index = idx
        pages.append(comic)

    context = RequestContext(request, {
        'pages': pages,
        'file_name': encoded,
        'nav': nav,
    })
    return HttpResponse(template.render(context))

def get_image(request, comic_path, page):
    base_dir = Setting.objects.get(name='BASE_DIR')
    comic_path = urlsafe_base64_decode(comic_path)
    if comic_path.lower().endswith('cbr'):
        cbx = rarfile.RarFile(path.join(base_dir.value, comic_path))
    elif comic_path.lower().endswith('cbz'):
        cbx = ZipFile(path.join(base_dir.value, comic_path))
    page = int(page)
    page_file = cbx.namelist()[page]
    file_name = str(page_file).lower()
    if file_name.endswith('jpg') or file_name.endswith('jpeg'):
        content = 'image/JPEG'
    elif file_name.endswith('png'):
        content = 'image/png'
    elif file_name.endswith('bmp'):
        content = 'image/bmp'
    elif file_name.endswith('gif'):
        content = 'image/gif'
    else:
        content = 'text/plain'
    try:
        img = cbx.open(file)
    except KeyError:
        img = cbx.open(page_file)
    return HttpResponse(img.read(), content_type=content)

class Breadcrumb:
    def __init__(self):
        self.name = 'Home'
        self.url = '/comic/'

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
        bc.url = prefix + urlsafe_base64_encode(item)
        output.append(bc)
        last = path.join(last, item)
    return output