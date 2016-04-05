from collections import OrderedDict
from os import path, listdir

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
        self.isdir = False
        self.icon = ''
        self.iscb = False
        self.location = ''
        self.label = ''
        self.cur_page = 0

    def __str__(self):
        return self.name


def generate_directory(user, directory=False):
    """

    :type user: User
    :type directory: Directory
    """
    base_dir = Setting.objects.get(name='BASE_DIR').value
    files = []
    if directory:
        dir_path = directory.path
        ordered_dir_list = get_ordered_dir_list(path.join(base_dir, directory.path))
    else:
        dir_path = ''
        ordered_dir_list = get_ordered_dir_list(base_dir)
    for file_name in ordered_dir_list:
        df = DirFile()
        df.name = file_name
        if path.isdir(path.join(base_dir, dir_path, file_name)):
            try:
                if directory:
                    d = Directory.objects.get(name=file_name,
                                              parent=directory)
                else:
                    d = Directory.objects.get(name=file_name,
                                              parent__isnull=True)
            except Directory.DoesNotExist:
                if directory:
                    d = Directory(name=file_name,
                                  parent=directory)
                else:
                    d = Directory(name=file_name)
                d.save()
            df.isdir = True
            df.icon = 'glyphicon-folder-open'
            df.location = '/comic/{0}/'.format(urlsafe_base64_encode(d.selector.bytes).decode())
            df.label = generate_dir_status(user, d)
        elif file_name.lower()[-4:] in ['.rar', '.zip', '.cbr', '.cbz']:
            df.iscb = True
            df.icon = 'glyphicon-book'
            try:
                if directory:
                    book = ComicBook.objects.get(file_name=file_name,
                                                 directory=directory)
                else:
                    book = ComicBook.objects.get(file_name=file_name,
                                                 directory__isnull=True)
            except ComicBook.DoesNotExist:
                book = ComicBook.process_comic_book(file_name, directory)

            status, _ = ComicStatus.objects.get_or_create(comic=book, user=user)
            last_page = status.last_read_page
            df.location = '/comic/read/{0}/{1}/'.format(urlsafe_base64_encode(book.selector.bytes).decode(),
                                                        last_page)
            if status.unread:
                df.label = '<center><span class="label label-default">Unread</span></center>'
            elif (last_page + 1) == book.page_count:
                df.label = '<center><span class="label label-success">Read</span></center>'
                df.cur_page = last_page
            else:
                label_text = '<center><span class="label label-primary">%s/%s</span></center>' % \
                             (last_page + 1, book.page_count)
                df.label = label_text
                df.cur_page = last_page

                # df.label = '<span class="label label-danger pull-right">Unprocessed</span>'
        files.append(df)
    return files


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


def scan_directory(directory=False):
    """
    TODO: Increase efficiency of this. reduce amount of queries.
    :type directory: Directory
    """
    base_dir = Setting.objects.get(name='BASE_DIR').value
    # filter(os.path.isdir, os.listdir(os.getcwd()))
    if directory:
        full_path = path.join(base_dir, directory.path)
    else:
        full_path = base_dir
    dir_list = listdir(full_path)
    directorys = [d for d in dir_list if path.isdir(path.join(full_path, d))]
    for direct in directorys:
        if directory:
            d, created = Directory.objects.get_or_create(name=direct,
                                                         parent=directory)
        else:
            d, created = Directory.objects.get_or_create(name=direct)
        if created:
            d.save()
