import json
import uuid
from os import path

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import SettingsForm, AccountForm, EditUserForm, AddUserForm, InitialSetupForm
from .models import Setting, ComicBook, ComicStatus, Directory, ComicPage
from .util import generate_breadcrumbs_from_path, generate_breadcrumbs_from_menu, \
    generate_title_from_path, Menu, generate_directory, scan_directory


@ensure_csrf_cookie
@login_required
def comic_list(request, directory_selector=False):
    try:
        base_dir = Setting.objects.get(name='BASE_DIR').value
    except Setting.DoesNotExist:
        return redirect('/comic/settings/')
    if not path.isdir(base_dir):
        return redirect('/comic/settings/')

    if directory_selector:
        selector = uuid.UUID(bytes=urlsafe_base64_decode(directory_selector))
        directory = Directory.objects.get(selector=selector)
    else:
        directory = False

    scan_directory(directory)

    if directory:
        title = generate_title_from_path(directory.path)
        breadcrumbs = generate_breadcrumbs_from_path(directory)
        json_url = '/comic/list_json/{0}/'.format(directory_selector)
    else:
        title = generate_title_from_path('Home')
        breadcrumbs = generate_breadcrumbs_from_path()
        json_url = '/comic/list_json/'
    files = generate_directory(request.user)

    return render(request, 'comic/comic_list.html', {
        'file_list': files,
        'breadcrumbs': breadcrumbs,
        'menu': Menu(request.user, 'Browse'),
        'title': title,
        'json_url': json_url
    })


@login_required
@require_POST
def comic_list_json(request, directory_selector=False):
    icon_str = '<span class="glyphicon {0}"></span>'
    if directory_selector:
        directory_selector = uuid.UUID(bytes=urlsafe_base64_decode(directory_selector))
        directory = Directory.objects.get(selector=directory_selector)
    else:
        directory = False
    files = generate_directory(request.user, directory)
    response_data = dict()
    response_data['data'] = []
    for file in files:
        response_data['data'].append({
            'icon': icon_str.format(file.icon),
            'name': file.name,
            'label': file.label,
            'url': file.location,
        })
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )



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
    context = {
        'form': form,
        'menu': Menu(request.user, 'Account'),
        'error_message': form.errors,
        'success_message': '</br>'.join(success_message),
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
        'title': 'CBWebReader - Account',
    }
    return render(request, 'comic/settings_page.html', context)


@user_passes_test(lambda u: u.is_superuser)
def users_page(request):
    users = User.objects.all()
    crumbs = [
        ('Users', '/comic/settings/users/'),
    ]
    context = {
        'users': users,
        'menu': Menu(request.user, 'Users'),
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
    }
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
    context = {
        'form': form,
        'users': users,
        'menu': Menu(request.user, 'Users'),
        'error_message': form.errors,
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
        'success_message': '</br>'.join(success_message),
        'title': 'CBWebReader - Edit User - ' + user.username,
    }
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
    context = {
        'form': form,
        'menu': Menu(request.user, 'Users'),
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
        'error_message': form.errors,
        'success_message': success_message,
        'title': 'CBWebReader - Add User',
    }
    return render(request, 'comic/settings_page.html', context)


@user_passes_test(lambda u: u.is_superuser)
def settings_page(request):
    success_message = []
    crumbs = [
        ('Settings', '/comic/settings/'),
    ]
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
    context = {
        'error_message': form.errors,
        'success_message': '</br>'.join(success_message),
        'form': form,
        'menu': Menu(request.user, 'Settings'),
        'title': 'CBWebReader - Settings',
        'breadcrumbs': generate_breadcrumbs_from_menu(crumbs),
    }
    return render(request, 'comic/settings_page.html', context)


@login_required
def read_comic(request, comic_selector, page):
    base_dir = Setting.objects.get(name='BASE_DIR').value
    page = int(page)
    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = get_object_or_404(ComicBook, selector=selector)

    breadcrumbs = generate_breadcrumbs_from_path(book.directory, book)

    status, _ = ComicStatus.objects.get_or_create(comic=book, user=request.user)
    status.unread = False
    status.last_read_page = page
    if ComicPage.objects.filter(Comic=book).aggregate(Max('index'))['index__max'] == status.last_read_page:
        status.finished = True
    else:
        status.finished = False
    status.save()
    title = 'CBWebReader - ' + book.file_name + ' - Page: ' + str(page)
    context = {
        'book': book,
        'orig_file_name': book.page_name(page),
        'nav': book.nav(page, request.user),
        'breadcrumbs': breadcrumbs,
        'menu': Menu(request.user),
        'title': title,
    }
    return render(request, 'comic/read_comic.html', context)


@login_required
def get_image(_, comic_selector, page):
    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = ComicBook.objects.get(selector=selector)
    img, content = book.get_image(int(page))
    return HttpResponse(img.read(), content_type=content)


def initial_setup(request):
    if User.objects.all().exists():
        return redirect('/comic/')
    if request.POST:
        form = InitialSetupForm(request.POST)
        if form.is_valid():
            user = User(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                is_staff=True,
                is_superuser=True,
            )
            user.set_password(form.cleaned_data['password'])
            user.save()
            base_dir, _ = Setting.objects.get_or_create(name='BASE_DIR')
            base_dir.value = form.cleaned_data['base_dir']
            base_dir.save()
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            login(request, user)
            return redirect('/comic/')
    else:
        form = InitialSetupForm()
    context = {
        'form': form,
        'title': 'CBWebReader - Setup',
        'error_message': form.errors,
    }
    return render(request, 'comic/settings_page.html', context)


def comic_redirect(_):
    return redirect('/comic/')
