from django.http import HttpResponse
from django.template import RequestContext
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from comic.models import Setting, ComicBook, ComicStatus
from util import generate_breadcrumbs
from forms import SettingsForm

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
    files = ComicBook.generate_directory(request.user, base_dir, comic_path)
    context = RequestContext(request, {
        'file_list': files,
        'breadcrumbs': breadcrumbs,
    })
    return render(request, 'comic/comic_list.html', context)


@login_required
def settings_page(request):
    error_message = ''

    if request.POST:
        form = SettingsForm(request.POST)
        if form.is_valid():
            if path.isdir(form.cleaned_data['base_dir']):
                base_dir = Setting.objects.get(name='BASE_DIR')
                base_dir.value = form.cleaned_data['base_dir']
                base_dir.save()
            else:
                error_message = 'This is not a valid Directory'
            recap = Setting.objects.get(name='RECAPTCHA')
            if form.cleaned_data['recaptcha']:
                recap.value = '1'
            else:
                recap.value = '0'
            recap.save()
            rprik = Setting.objects.get(name='RECAPTCHA_PRIVATE_KEY')
            rprik.value = form.cleaned_data['recaptcha_private_key']
            rprik.save()
            rpubk = Setting.objects.get(name='RECAPTCHA_PUBLIC_KEY')
            rpubk.value = form.cleaned_data['recaptcha_public_key']
            rpubk.save()
    form = SettingsForm(initial=SettingsForm.get_initial_values())
    context = RequestContext(request, {
        'error_message': error_message,
        'form': form,
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
    status, _ = ComicStatus.objects.get_or_create(comic=book, user=request.user)
    status.unread = False
    status.last_read_page = page
    status.save()
    context = RequestContext(request, {
        'book': book,
        'orig_file_name': book.page_name(page),
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