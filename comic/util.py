from dataclasses import dataclass

from comic.models import ComicBook, Directory


@dataclass()
class Breadcrumb:
    name: str = 'Home'
    selector: str = ''


def generate_breadcrumbs_from_path(
        directory: Directory | None = None,
        book: ComicBook | None = None,
) -> list[Breadcrumb]:
    output = [Breadcrumb()]
    folders = directory.get_path_objects() if directory else []
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
