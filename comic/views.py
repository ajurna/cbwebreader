from django.http import HttpResponse
from django.template import RequestContext
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from comic.models import Setting, ComicBook, ComicStatus
from util import generate_breadcrumbs_from_path, generate_breadcrumbs_from_menu
from forms import SettingsForm, AccountForm, EditUserForm, AddUserForm
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
    files = ComicBook.generate_directory(request.user, base_dir, comic_path)
    context = RequestContext(request, {
        'file_list': files,
        'breadcrumbs': generate_breadcrumbs_from_path(comic_path),
        'menu': Menu(request.user, 'Browse'),
    })
    return render(request, 'comic/comic_list.html', context)


@login_required
def account_page(request):
    success_message = []
    if request.POST:
        form = AccountForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['email'] != request.user.email:
                request.user.email = form.cleaned_data['email']
                success_message.append('Email Updated.')
            if len(form.cleaned_data['password']) != 0:
                request.user.set_password(form.cleaned_data['password'])
                success_message.append('Password Updated.')
            request.user.save()
    else:
        form = AccountForm(initial={
            'username': request.user.username,
            'email': request.user.email,
        })
    crumbs = [
        ('Account', '/comic/account/'),
    ]
    context = RequestContext(request, {
        'form': form,
        'menu': Menu(request.user, 'Account'),
        'error_message': form.errors,
        'success_message': '</br>'.join(success_message),
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
    })
    return render(request, 'comic/settings_page.html', context)


@user_passes_test(lambda u: u.is_superuser)
def users_page(request):
    users = User.objects.all()
    crumbs = [
        ('Users', '/comic/settings/users/'),
    ]
    context = RequestContext(request, {
        'users': users,
        'menu': Menu(request.user, 'Users'),
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
    })
    return render(request, 'comic/users_page.html', context)


@user_passes_test(lambda u: u.is_superuser)
def user_config_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    success_message = []
    if request.POST:
        form = EditUserForm(request.POST)
        if form.is_valid():
            if 'password' in form.cleaned_data:
                if len(form.cleaned_data['password']) != 0:
                    user.set_password(form.cleaned_data['password'])
                    success_message.append('Password Updated.')
            if form.cleaned_data['email'] != user.email:
                user.email = form.cleaned_data['email']
                success_message.append('Email Updated.</br>')
            user.save()
    else:
        form = EditUserForm(initial=EditUserForm.get_initial_values(user))

    users = User.objects.all()
    crumbs = [
        ('Users', '/comic/settings/users/'),
        (user.username, '/comic/settings/users/' + str(user.id)),
    ]
    context = RequestContext(request, {
        'form': form,
        'users': users,
        'menu': Menu(request.user, 'Users'),
        'error_message': form.errors,
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
        'success_message': '</br>'.join(success_message),
    })
    return render(request, 'comic/settings_page.html', context)


@user_passes_test(lambda u: u.is_superuser)
def user_add_page(request):
    success_message = ''
    if request.POST:
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = User(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
            )
            user.set_password(form.cleaned_data['password'])
            user.save()
            success_message = 'User {} created.'.format(user.username)

    else:
        form = AddUserForm()
    crumbs = [
        ('Users', '/comic/settings/users/'),
        ('Add', '/comic/settings/users/add/'),
    ]
    context = RequestContext(request, {
        'form': form,
        'menu': Menu(request.user, 'Users'),
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
        'error_message': form.errors,
        'success_message': success_message,
    })
    return render(request, 'comic/settings_page.html', context)


@user_passes_test(lambda u: u.is_superuser)
def settings_page(request):
    success_message = []
    if request.POST:
        form = SettingsForm(request.POST)
        if form.is_valid():
            base_dir = Setting.objects.get(name='BASE_DIR')
            base_dir.value = form.cleaned_data['base_dir']
            base_dir.save()
            recap = Setting.objects.get(name='RECAPTCHA')
            if form.cleaned_data['recaptcha']:
                recap.value = '1'
            else:
                recap.value = '0'
            recap.save()
            recaptcha_private_key = Setting.objects.get(name='RECAPTCHA_PRIVATE_KEY')
            recaptcha_private_key.value = form.cleaned_data['recaptcha_private_key']
            recaptcha_private_key.save()
            recaptcha_public_key = Setting.objects.get(name='RECAPTCHA_PUBLIC_KEY')
            recaptcha_public_key.value = form.cleaned_data['recaptcha_public_key']
            recaptcha_public_key.save()
            success_message.append('Settings updated.')
    form = SettingsForm(initial=SettingsForm.get_initial_values())
    context = RequestContext(request, {
        'error_message': form.errors,
        'success_message': '</br>'.join(success_message),
        'form': form,
        'menu': Menu(request.user, 'Settings'),
    })
    return render(request, 'comic/settings_page.html', context)


@login_required
def read_comic(request, comic_path, page):
    base_dir = Setting.objects.get(name='BASE_DIR').value
    page = int(page)
    decoded_path = urlsafe_base64_decode(comic_path)
    breadcrumbs = generate_breadcrumbs_from_path(decoded_path)
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