"""Shared helpers for listing the pages inside a comic archive."""

import mimetypes
import zipfile
from typing import NamedTuple

import rarfile


class ArchiveFile(NamedTuple):
    file_name: str
    mime_type: str


def get_archive_files(archive: zipfile.ZipFile | rarfile.RarFile) -> list[ArchiveFile]:
    """Return the image entries of an archive in page order.

    Metadata entries such as ComicInfo.xml are not pages. Counting them would make
    page_count disagree with the page list the reader uses, so a book could never
    be marked as finished.
    """
    result = []
    for name in sorted(archive.namelist()):
        if name.endswith('/'):
            continue
        mime_type = mimetypes.guess_type(name)[0]
        if not mime_type or name.lower().endswith('.xml'):
            continue
        result.append(ArchiveFile(name, mime_type))
    return result
