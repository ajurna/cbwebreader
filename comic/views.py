from django.http import HttpResponse
from django.template import RequestContext
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from comic.models import Setting, ComicBook
from util import generate_breadcrumbs

from os import path

@login_required
def comic_list(request, comic_path=''):
    try:
        base_dir = Setting.objects.get(name='BASE_DIR').value
    except Setting.DoesNotExist:
        return redirect('/comic/settings/')
    if not path.isdir(base_dir):
        return redirect('/comic/settings/')
    comic_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs(comic_path)
    files = ComicBook.generate_directory(base_dir, comic_path)
    context = RequestContext(request, {
        'file_list': files,
        'breadcrumbs': breadcrumbs,
    })
    return render(request, 'comic/comic_list.html', context)

@login_required
def settings_page(request):
    obj, created = Setting.objects.get_or_create(name='BASE_DIR')
    error_message = ''
    if request.POST:
        if path.isdir(request.POST['base_directory']):
            obj.value = request.POST['base_directory']
            obj.save()
        else:
            error_message = 'This is not a valid Directory'
    elif obj.value == '':
        error_message = 'Base Directory cannot be blank'
    elif not path.isdir(obj.value):
        error_message = 'Base Directory does not exist'
    context = RequestContext(request, {
        'base_dir': obj,
        'error_message': error_message,
    })
    return render(request, 'comic/settings_page.html', context)

@login_required
def read_comic(request, comic_path, page):
    base_dir = Setting.objects.get(name='BASE_DIR').value
    page = int(page)
    decoded_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs(decoded_path)
    _, comic_file_name = path.split(decoded_path)
    try:
        book = ComicBook.objects.get(file_name=comic_file_name)
    except ComicBook.DoesNotExist:
        book = ComicBook.process_comic_book(base_dir, decoded_path, comic_file_name)
    book.unread = False
    book.last_read_page = page
    book.save()
    context = RequestContext(request, {
        'book': book,
        'orig_file_name': book.pages()[page].name,
        'nav': book.nav(comic_path, page),
        'breadcrumbs': breadcrumbs,
    })
    return render(request, 'comic/read_comic.html', context)

@login_required
def get_image(_, comic_path, page):
    base_dir = Setting.objects.get(name='BASE_DIR').value
    page = int(page)
    decoded_path = urlsafe_base64_decode(comic_path)
    _, comic_file_name = path.split(decoded_path)
    try:
        book = ComicBook.objects.get(file_name=comic_file_name)
    except ComicBook.DoesNotExist:
        book = ComicBook.process_comic_book(base_dir, decoded_path, comic_file_name)
    full_path = path.join(base_dir, decoded_path)
    img, content = book.get_image(full_path, page)
    return HttpResponse(img.read(), content_type=content)


def comic_redirect(_):
    return redirect('/comic/')