from django.http import HttpResponse
from django.template import RequestContext
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from comic.models import Setting, ComicBook, ComicStatus
from util import generate_breadcrumbs
from forms import SettingsForm, AccountForm
from util import Menu
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
        'menu': Menu(request.user, 'Browse'),
    })
    return render(request, 'comic/comic_list.html', context)

@login_required
def account_page(request):
    error_message = []
    success_message = []
    if request.POST:
        form = AccountForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password1'] != '':
                if form.cleaned_data['password1'] == form.cleaned_data['password2']:
                    if len(form.cleaned_data['password1']) < 8:
                        error_message.append('Password is too short')
                    else:
                        success_message.append('password changed')
                        request.user.set_password(form.cleaned_data['password1'])
                else:
                    error_message.append("Passwords don't match")
            if form.cleaned_data['email'] != request.user.email:
                try:
                    validate_email(form.cleaned_data['email'])
                    success_message.append('Email Address updated')
                    request.user.email = form.cleaned_data['email']
                except ValidationError:
                    error_message.append('Invalid E-mail.')
            request.user.save()
    else:
        form = AccountForm(initial={
            'username': request.user.username,
            'email': request.user.email,
        })
    context = RequestContext(request, {
        'form': form,
        'menu': Menu(request.user, 'Account'),
        'error_message': '</br>'.join(error_message),
        'success_message': '</br>'.join(success_message),
    })
    return render(request, 'comic/settings_page.html', context)

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
        'menu': Menu(request.user, 'Settings')
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
        'menu': Menu(request.user)
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