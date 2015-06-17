from django.http import HttpResponse
from django.template import RequestContext, loader
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render

from comic.models import Setting
from util import generate_breadcrumbs, generate_directory

from unrar import rarfile
from zipfile import ZipFile
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

def index(request, comic_path=''):
    base_dir = Setting.objects.get(name='BASE_DIR')
    comic_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs(comic_path)
    files = generate_directory(base_dir, comic_path)
    context = RequestContext(request, {
        'file_list': files,
        'breadcrumbs': breadcrumbs,
    })
    return render(request, 'comic/index.html', context)


def read_comic(request, comic_path, page):
    encoded = comic_path
    comic_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs(comic_path)
    base_dir = Setting.objects.get(name='BASE_DIR')
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
        'orig_file_name': pages[nav.cur].name,
        'nav': nav,
        'breadcrumbs': breadcrumbs,
    })
    return render(request, 'comic/read_comic.html', context)


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


