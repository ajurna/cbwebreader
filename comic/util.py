from dataclasses import dataclass

from .models import ComicBook, Directory


@dataclass()
class Breadcrumb:
    name: str = 'Home'
    selector: str = ''


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
        output.append(
            Breadcrumb(
                name=item.name,
                selector=item.selector
            )
        )
    if book:
        output.append(
            Breadcrumb(
                name=book.file_name,
                selector=book.selector
            )
        )
    return output
