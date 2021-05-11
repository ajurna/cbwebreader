import json
import uuid

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Max, Count, F
from django.db.transaction import atomic
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import AccountForm, AddUserForm, EditUserForm, InitialSetupForm, DirectoryEditForm
from .models import ComicBook, ComicPage, ComicStatus, Directory
from .util import (
    Menu,
    generate_breadcrumbs_from_menu,
    generate_breadcrumbs_from_path,
    generate_directory,
    generate_label,
    generate_title_from_path,
)


# noinspection PyTypeChecker
@ensure_csrf_cookie
@login_required
def comic_list(request, directory_selector=False):
    if User.objects.all().count() == 0:
        return redirect("/comic/settings/")

    directory = None
    if directory_selector:
        selector = uuid.UUID(bytes=urlsafe_base64_decode(directory_selector))
        directory = Directory.objects.get(selector=selector)

    if directory:
        title = generate_title_from_path(directory.path)
        breadcrumbs = generate_breadcrumbs_from_path(directory)
    else:
        title = generate_title_from_path("Home")
        breadcrumbs = generate_breadcrumbs_from_path()

    files = generate_directory(request.user, directory)
    form = DirectoryEditForm()

    return render(
        request,
        "comic/comic_list.html",
        {
            "breadcrumbs": breadcrumbs,
            "menu": Menu(request.user, "Browse"),
            "title": title,
            "files": files,
            "form": form,
            "selector": directory_selector if directory_selector else 'None',
            'js_urls': {
                "perform_action": reverse('perform_action', args=('operation', 'item_type', 'selector'))
            }
        },
    )


@login_required
def perform_action(request, operation, item_type, selector):
    if operation not in ['mark_read', 'mark_unread', 'mark_previous', 'set_classification']:
        return HttpResponse(400)
    elif operation == 'mark_previous' and item_type == 'Directory':
        return HttpResponse(422)
    try:
        selector_uuid = uuid.UUID(bytes=urlsafe_base64_decode(selector))
    except ValueError:
        if item_type == 'Directory':
            for book in ComicBook.objects.filter(directory__isnull=True):
                getattr(book, operation)(request.user)
            return HttpResponse(204)
        else:
            return HttpResponse(400)
    if operation == 'set_classification':
        form = DirectoryEditForm(request.POST)
        if form.is_valid() and item_type == 'Directory':
            pass
        else:
            return HttpResponse(400)
    if item_type == 'ComicBook':
        book = get_object_or_404(ComicBook, selector=selector_uuid)
        getattr(book, operation)(request.user)
        return HttpResponse(204)
    elif item_type == 'Directory':
        directory = get_object_or_404(Directory, selector=selector_uuid)
        if operation == 'set_classification':
            getattr(directory, operation)(form.cleaned_data)
        else:
            getattr(directory, operation)(request.user)
        return HttpResponse(204)


@login_required
def recent_comics(request):
    return render(
        request,
        "comic/recent_comics.html",
        {
            "breadcrumbs": generate_breadcrumbs_from_menu([("Recent", "/comic/recent/")]),
            "menu": Menu(request.user, "Recent"),
            "title": "Recent Comics",
            "feed_id": urlsafe_base64_encode(request.user.usermisc.feed_id.bytes),
        },
    )


@login_required
@require_POST
def recent_comics_json(request):
    start = int(request.POST["start"])
    end = start + int(request.POST["length"])
    icon = '<span class="fa fa-book"></span>'
    comics = ComicBook.objects.all().annotate(total_pages=Count('comicpage'))
    response_data = dict()
    response_data["recordsTotal"] = comics.count()
    if request.POST["search[value]"]:
        comics = comics.filter(file_name__contains=request.POST["search[value]"])
    order_string = ""
    # Ordering
    if request.POST["order[0][dir]"] == "desc":
        order_string += "-"
    if request.POST["order[0][dir]"] == "3":
        order_string += "date_added"
    elif request.POST["order[0][dir]"] == "2":
        order_string += "date_added"
    else:
        order_string += "date_added"
    comics = comics.order_by(order_string)
    comics = comics.filter(comicstatus__user=request.user).annotate(
        unread=F('comicstatus__unread'),
        finished=F('comicstatus__finished'),
        last_read_page=F('comicstatus__last_read_page')
    )
    response_data["recordsFiltered"] = comics.count()
    response_data["data"] = list()
    for book in comics[start:end]:
        response_data["data"].append(
            {
                "selector": urlsafe_base64_encode(book.selector.bytes),
                "icon": icon,
                "type": "book",
                "name": book.file_name,
                "date": book.date_added.strftime("%d/%m/%y-%H:%M"),
                "label": generate_label(book),
                "url": "/comic/read/{0}/".format(urlsafe_base64_encode(book.selector.bytes)),
            }
        )
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@login_required
@require_POST
def comic_edit(request):
    if "selected" not in request.POST:
        return HttpResponse(status=200)
    if request.POST["func"] == "choose":
        return HttpResponse(status=200)
    selected = [uuid.UUID(bytes=urlsafe_base64_decode(item)) for item in request.POST.getlist("selected")]
    comics = ComicBook.objects.filter(selector__in=selected)
    with atomic():
        for comic in comics:
            status, _ = ComicStatus.objects.get_or_create(comic=comic, user=request.user)
            if request.POST["func"] == "read":
                status.unread = False
                status.finished = True
                status.last_read_page = comic.page_count - 1
            elif request.POST["func"] == "unread":
                status.unread = True
                status.finished = False
                status.last_read_page = 0
            status.save()
    return HttpResponse(status=200)


@login_required
def account_page(request):
    success_message = []
    if request.POST:
        form = AccountForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["email"] != request.user.email:
                request.user.email = form.cleaned_data["email"]
                success_message.append("Email Updated.")
            if len(form.cleaned_data["password"]) != 0:
                request.user.set_password(form.cleaned_data["password"])
                success_message.append("Password Updated.")
            request.user.save()
    else:
        form = AccountForm(initial={"username": request.user.username, "email": request.user.email})
    crumbs = [("Account", "/comic/account/")]
    context = {
        "form": form,
        "menu": Menu(request.user, "Account"),
        "error_message": form.errors,
        "success_message": "</br>".join(success_message),
        "breadcrumbs": generate_breadcrumbs_from_menu(crumbs),
        "title": "CBWebReader - Account",
    }
    return render(request, "comic/settings_page.html", context)


@user_passes_test(lambda u: u.is_superuser)
def users_page(request):
    users = User.objects.all().select_related('usermisc')
    crumbs = [("Users", "/comic/settings/users/")]
    context = {
        "users": users,
        "menu": Menu(request.user, "Users"),
        "breadcrumbs": generate_breadcrumbs_from_menu(crumbs),
    }
    return render(request, "comic/users_page.html", context)


@user_passes_test(lambda u: u.is_superuser)
def user_config_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    success_message = []
    if request.POST:
        form = EditUserForm(request.POST)
        if form.is_valid():
            if "password" in form.cleaned_data:
                if len(form.cleaned_data["password"]) != 0:
                    user.set_password(form.cleaned_data["password"])
                    success_message.append("Password Updated.")
            if form.cleaned_data["email"] != user.email:
                user.email = form.cleaned_data["email"]
                success_message.append("Email Updated.</br>")
            user.usermisc.allowed_to_read = form.cleaned_data['allowed_to_read']
            user.usermisc.save()
            user.save()
    else:
        form = EditUserForm(initial=EditUserForm.get_initial_values(user))

    users = User.objects.all()
    crumbs = [("Users", "/comic/settings/users/"), (user.username, "/comic/settings/users/" + str(user.id))]
    context = {
        "form": form,
        "users": users,
        "menu": Menu(request.user, "Users"),
        "error_message": form.errors,
        "breadcrumbs": generate_breadcrumbs_from_menu(crumbs),
        "success_message": "</br>".join(success_message),
        "title": "CBWebReader - Edit User - " + user.username,
    }
    return render(request, "comic/settings_page.html", context)


@user_passes_test(lambda u: u.is_superuser)
def user_add_page(request):
    success_message = ""
    if request.POST:
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = User(username=form.cleaned_data["username"], email=form.cleaned_data["email"])
            user.set_password(form.cleaned_data["password"])
            user.save()
            success_message = "User {} created.".format(user.username)

    else:
        form = AddUserForm()
    crumbs = [("Users", "/comic/settings/users/"), ("Add", "/comic/settings/users/add/")]
    context = {
        "form": form,
        "menu": Menu(request.user, "Users"),
        "breadcrumbs": generate_breadcrumbs_from_menu(crumbs),
        "error_message": form.errors,
        "success_message": success_message,
        "title": "CBWebReader - Add User",
    }
    return render(request, "comic/settings_page.html", context)


@login_required
def read_comic(request, comic_selector):

    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = get_object_or_404(ComicBook, selector=selector)
    if book.directory.classification > request.user.usermisc.allowed_to_read:
        return redirect('index')

    pages = ComicPage.objects.filter(Comic=book)

    status, _ = ComicStatus.objects.get_or_create(comic=book, user=request.user)
    title = "CBWebReader - " + book.file_name
    context = {
        "book": book,
        "pages": pages,
        "nav": book.nav(request.user),
        "status": status,
        "breadcrumbs": generate_breadcrumbs_from_path(book.directory, book),
        "menu": Menu(request.user),
        "title": title,
    }
    if book.file_name.lower().endswith('pdf'):
        context['status'].last_read_page += 1
        return render(request, "comic/read_comic_pdf.html", context)
    else:
        book.verify_pages(pages)
        context['pages'] = ComicPage.objects.filter(Comic=book)
        return render(request, "comic/read_comic.html", context)


@login_required
def set_read_page(request, comic_selector, page):
    page = int(page)
    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = get_object_or_404(ComicBook, selector=selector)
    status, _ = ComicStatus.objects.get_or_create(comic=book, user=request.user)
    status.unread = False
    status.last_read_page = page
    if ComicPage.objects.filter(Comic=book).aggregate(Max("index"))["index__max"] == status.last_read_page:
        status.finished = True
    else:
        status.finished = False
    status.save()
    return HttpResponse(status=200)


@xframe_options_sameorigin
@login_required
def get_image(request, comic_selector, page):
    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = ComicBook.objects.get(selector=selector)
    if book.directory.classification > request.user.usermisc.allowed_to_read:
        return HttpResponse(status=401)
    img, content = book.get_image(int(page))
    return FileResponse(img, content_type=content)


@xframe_options_sameorigin
@login_required
def comic_thumbnail(request, comic_selector):
    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = ComicBook.objects.get(selector=selector)
    if book.directory.classification > request.user.usermisc.allowed_to_read:
        return HttpResponse(status=401)
    return redirect(book.get_thumbnail_url())


@xframe_options_sameorigin
@login_required
def directory_thumbnail(request, directory_selector):
    selector = uuid.UUID(bytes=urlsafe_base64_decode(directory_selector))
    folder = Directory.objects.get(selector=selector)
    if folder.classification > request.user.usermisc.allowed_to_read:
        return HttpResponse(status=401)
    return redirect(folder.get_thumbnail_url())


@login_required
def get_pdf(request, comic_selector):
    selector = uuid.UUID(bytes=urlsafe_base64_decode(comic_selector))
    book = ComicBook.objects.get(selector=selector)
    if book.directory.classification > request.user.usermisc.allowed_to_read:
        return HttpResponse(status=401)
    return FileResponse(open(book.get_pdf(), 'rb'), content_type='application/pdf')


def initial_setup(request):
    if User.objects.all().exists():
        return redirect("/comic/")
    if request.POST:
        form = InitialSetupForm(request.POST)
        if form.is_valid():
            user = User(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                is_staff=True,
                is_superuser=True,
            )
            user.set_password(form.cleaned_data["password"])
            user.save()
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            login(request, user)
            return redirect("/comic/")
    else:
        form = InitialSetupForm()
    context = {"form": form, "title": "CBWebReader - Setup", "error_message": form.errors}
    return render(request, "comic/settings_page.html", context)


def comic_redirect(_):
    return redirect("/comic/")
