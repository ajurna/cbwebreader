from dataclasses import dataclass
from typing import Optional

from comic.models import ComicBook, Directory


@dataclass()
class Breadcrumb:
    name: str = 'Home'
    selector: str = ''


def generate_breadcrumbs_from_path(directory: Optional[Directory] = None, book: Optional[ComicBook] = None):
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
