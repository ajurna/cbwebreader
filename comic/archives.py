"""Shared helpers for listing the pages inside a comic archive."""

import mimetypes
import xml.etree.ElementTree as ElementTree
import zipfile
from typing import NamedTuple

import rarfile


class ArchiveFile(NamedTuple):
    file_name: str
    mime_type: str


# ComicInfo.xml is the ComicRack/ComicInfo schema. Only the fields the reader can show are
# read; the rest of the schema (Summary, Genre, PageCount, ...) is left alone.
COMIC_INFO_FIELDS = {
    'Title': 'metadata_title',
    'Series': 'series',
    'Number': 'issue_number',
    'Writer': 'writer',
    'Artist': 'artist',
    'Year': 'year',
}


def read_metadata(archive: zipfile.ZipFile | rarfile.RarFile) -> dict:
    """Return the ComicInfo.xml fields of an archive, or an empty dict if there is none.

    Values are strings except Year, which is an integer when it parses. Empty elements are
    skipped so a book with an empty ComicInfo.xml looks the same as a book without one.
    """
    name = next((entry for entry in sorted(archive.namelist()) if entry.lower().endswith('comicinfo.xml')), None)
    if name is None:
        return {}
    try:
        root = ElementTree.fromstring(archive.read(name).decode('utf-8', errors='replace'))
    except ElementTree.ParseError:
        return {}

    metadata = {}
    for element in root:
        key = COMIC_INFO_FIELDS.get(element.tag)
        if key is None:
            continue
        value = (element.text or '').strip()
        if not value:
            continue
        if key == 'year':
            try:
                metadata[key] = int(value)
            except ValueError:
                continue
        else:
            metadata[key] = value
    return metadata


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
