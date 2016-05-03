from collections import OrderedDict
from os import path, listdir

from django.db.transaction import atomic
from django.utils.http import urlsafe_base64_encode

from .models import ComicBook, Setting, ComicStatus, Directory


def generate_title_from_path(file_path):
    if file_path == '':
        return 'CBWebReader'
    return 'CBWebReader - ' + ' - '.join(file_path.split(path.sep))


class Menu:
    def __init__(self, user, page=''):
        """

        :type page: str
        """
        self.menu_items = OrderedDict()
        self.menu_items['Browse'] = '/comic/'
        self.menu_items['Recent'] = '/comic/recent/'
        self.menu_items['Account'] = '/comic/account/'
        if user.is_superuser:
            self.menu_items['Settings'] = '/comic/settings/'
            self.menu_items['Users'] = '/comic/settings/users/'
        self.menu_items['Logout'] = '/logout/'
        self.current_page = page


class Breadcrumb:
    def __init__(self):
        self.name = 'Home'
        self.url = '/comic/'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


def generate_breadcrumbs_from_path(directory=False, book=False):
    """

    :type directory: Directory
    :type book: ComicBook
    """
    output = [Breadcrumb()]
    if directory:
        folders = directory.get_path_objects()
    else:
        folders = []
    for item in folders[::-1]:
        bc = Breadcrumb()
        bc.name = item.name
        bc.url = b'/comic/' + urlsafe_base64_encode(item.selector.bytes)
        output.append(bc)
    if book:
        bc = Breadcrumb()
        bc.name = book.file_name
        bc.url = b'/read/' + urlsafe_base64_encode(book.selector.bytes)
        output.append(bc)

    return output


def generate_breadcrumbs_from_menu(paths):
    output = [Breadcrumb()]
    for item in paths:
        bc = Breadcrumb()
        bc.name = item[0]
        bc.url = item[1]
        output.append(bc)
    return output


class DirFile:
    def __init__(self):
        self.name = ''
        self.icon = ''
        self.location = ''
        self.label = ''
        self.type = ''
        self.selector = ''

    def __str__(self):
        return self.name

    def populate_directory(self, directory, user):
        self.name = directory.name
        self.icon = 'glyphicon-folder-open'
        self.selector = urlsafe_base64_encode(directory.selector.bytes).decode()
        self.location = '/comic/{0}/'.format(self.selector)
        self.label = generate_dir_status(user, directory)
        self.type = 'directory'

    def populate_comic(self, comic, user):
        self.icon = 'glyphicon-book'
        self.name = comic.file_name
        status, created = ComicStatus.objects.get_or_create(comic=comic, user=user)
        if created:
            status.save()
        self.selector = urlsafe_base64_encode(comic.selector.bytes).decode()
        self.location = '/comic/read/{0}/{1}/'.format(self.selector,
                                                      status.last_read_page)
        self.label = generate_label(comic, status)
        self.type = 'book'


def generate_directory(user, directory=False):
    """
    :type user: User
    :type directory: Directory
    """
    base_dir = Setting.objects.get(name='BASE_DIR').value
    files = []
    if directory:
        ordered_dir_list = listdir(path.join(base_dir, directory.path))
        dir_list = [x for x in ordered_dir_list if path.isdir(path.join(base_dir, directory.path, x))]
    else:
        ordered_dir_list = listdir(base_dir)
        dir_list = [x for x in ordered_dir_list if path.isdir(path.join(base_dir, x))]
    file_list = [x for x in ordered_dir_list if x not in dir_list]
    if directory:
        dir_list_obj = Directory.objects.filter(name__in=dir_list,
                                                parent=directory)
        file_list_obj = ComicBook.objects.filter(file_name__in=file_list,
                                                 directory=directory)
    else:
        dir_list_obj = Directory.objects.filter(name__in=dir_list,
                                                parent__isnull=True)
        file_list_obj = ComicBook.objects.filter(file_name__in=file_list,
                                                 directory__isnull=True)
    for directory_obj in dir_list_obj:
        df = DirFile()
        df.populate_directory(directory_obj, user)
        files.append(df)
        dir_list.remove(directory_obj.name)
    with atomic():
        for file_obj in file_list_obj:
            df = DirFile()
            df.populate_comic(file_obj, user)
            files.append(df)
            file_list.remove(file_obj.file_name)
        for directory_name in dir_list:
            if directory:
                directory_obj = Directory(name=directory_name,
                                          parent=directory)
            else:
                directory_obj = Directory(name=directory_name,
                                          parent__isnull=True)
            directory_obj.save()
            df = DirFile()
            df.populate_directory(directory_obj, user)
            files.append(df)
        for file_name in file_list:
            if file_name.lower()[-4:] in ['.rar', '.zip', '.cbr', '.cbz']:
                book = ComicBook.process_comic_book(file_name, directory)
                df = DirFile()
                df.populate_comic(book, user)
                files.append(df)
    return files


def generate_label(book, status):
    if status.unread:
        label_text = '<center><span class="label label-default">Unread</span></center>'
    elif (status.last_read_page + 1) == book.page_count:
        label_text = '<center><span class="label label-success">Read</span></center>'
    else:
        label_text = '<center><span class="label label-primary">%s/%s</span></center>' % \
                     (status.last_read_page + 1, book.page_count)
    return label_text


def generate_dir_status(user, directory):
    cb_list = ComicBook.objects.filter(directory=directory)
    total = cb_list.count()
    total_read = ComicStatus.objects.filter(user=user,
                                            comic__in=cb_list,
                                            finished=True).count()
    if total == 0:
        return '<center><span class="label label-default">Empty</span></center>'
    elif total == total_read:
        return '<center><span class="label label-success">All Read</span></center>'
    elif total_read == 0:
        return '<center><span class="label label-default">Unread</span></center>'
    return '<center><span class="label label-primary">{0}/{1}</span></center>'.format(total_read, total)


def get_ordered_dir_list(folder):
    directories = []
    files = []
    for item in listdir(folder):
        if path.isdir(path.join(folder, item)):
            directories.append(item)
        else:
            files.append(item)
    return sorted(directories) + sorted(files)
