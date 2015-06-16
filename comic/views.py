from django.http import HttpResponse
from django.template import RequestContext, loader
from comic.models import Setting

from unrar import rarfile
from zipfile import ZipFile
import os

class Comic:
    def __init__(self):
        self.name = ''
        self.index = 0
class Navigation:
    def __init__(self):
        self.next = 0
        self.prev = 0
        self.cur = 0
# Create your views here.
def index(request):
    base_dir = Setting.objects.get(name='BASE_DIR')
    files = os.listdir(base_dir.value)
    template = loader.get_template('comic/index.html')
    context = RequestContext(request, {
        'file_list': files,
    })

    return HttpResponse(template.render(context))


def read_comic(request, file_name, page):
    base_dir = Setting.objects.get(name='BASE_DIR')
    template = loader.get_template('comic/read_comic.html')
    if file_name.lower().endswith('cbr'):
        cbx = rarfile.RarFile(os.path.join(base_dir.value, file_name))
    elif file_name.lower().endswith('cbz'):
        cbx = ZipFile(os.path.join(base_dir.value, file_name))
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

    img_src = '/comic/file/0/' + file_name + '/img'
    context = RequestContext(request, {
        'pages': pages,
        'file_name': file_name,
        'img_src': img_src,
        'nav': nav,
    })
    return HttpResponse(template.render(context))

def get_image(request, file_name, page):
    base_dir = Setting.objects.get(name='BASE_DIR')
    if file_name.lower().endswith('cbr'):
        cbx = rarfile.RarFile(os.path.join(base_dir.value, file_name))
    elif file_name.lower().endswith('cbz'):
        cbx = ZipFile(os.path.join(base_dir.value, file_name))
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
