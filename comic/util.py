from django.utils.http import urlsafe_base64_encode

from os import path
from collections import OrderedDict
import os


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


def generate_breadcrumbs(comic_path):
    output = [Breadcrumb()]
    prefix = '/comic/'
    last = ''
    comic_path = path.normpath(comic_path)
    folders = comic_path.split(os.sep)
    for item in folders:
        if item == '.':
            continue
        bc = Breadcrumb()
        bc.name = item
        last = path.join(last, item)
        bc.url = prefix + urlsafe_base64_encode(last)
        output.append(bc)
    return output


def get_ordered_dir_list(folder):
    directories = []
    files = []
    for item in os.listdir(folder):
        if path.isdir(path.join(folder, item)):
            directories.append(item)
        else:
            files.append(item)
    return sorted(directories) + sorted(files)
