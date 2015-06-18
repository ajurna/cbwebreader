from django.http import HttpResponse
from django.template import RequestContext
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render

from comic.models import Setting, ComicBook
from util import generate_breadcrumbs, generate_directory, process_comic_book

from os import path

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
    base_dir = Setting.objects.get(name='BASE_DIR')
    page = int(page)
    decoded_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs(decoded_path)
    _, comic_file_name = path.split(decoded_path)
    try:
        book = ComicBook.objects.get(file_name=comic_file_name)
    except ComicBook.DoesNotExist:
        book = process_comic_book(base_dir, decoded_path, comic_file_name)
    book.last_read_page = page
    book.save()
    context = RequestContext(request, {
        'book': book,
        'orig_file_name': book.pages()[page].name,
        'nav': book.nav(comic_path, page),
        'breadcrumbs': breadcrumbs,
    })
    return render(request, 'comic/read_comic.html', context)


def get_image(request, comic_path, page):
    base_dir = Setting.objects.get(name='BASE_DIR')
    page = int(page)
    decoded_path = urlsafe_base64_decode(comic_path)
    _, comic_file_name = path.split(decoded_path)
    try:
        book = ComicBook.objects.get(file_name=comic_file_name)
    except ComicBook.DoesNotExist:
        book = process_comic_book(base_dir, decoded_path, comic_file_name)
    full_path = path.join(base_dir.value, decoded_path)
    img, content = book.get_image(full_path, page)
    return HttpResponse(img.read(), content_type=content)
