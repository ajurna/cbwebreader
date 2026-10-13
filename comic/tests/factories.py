"""Helpers for creating comic files on disk."""

import io
import zipfile
from pathlib import Path

import pymupdf
from PIL import Image


def make_cbz(path: Path, pages: int = 3, metadata: bool = True) -> Path:
    """Write a .cbz containing PNG pages and, optionally, a ComicInfo.xml."""
    with zipfile.ZipFile(path, 'w') as archive:
        for page in range(pages):
            image = Image.new('RGB', (10, 10))
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            archive.writestr(f'page{page:02}.png', buffer.getvalue())
        if metadata:
            archive.writestr('ComicInfo.xml', '<ComicInfo><Title>Test</Title></ComicInfo>')
    return path


def make_pdf(path: Path, pages: int = 2) -> Path:
    """Write a PDF with the given number of pages."""
    document = pymupdf.open()
    for _ in range(pages):
        document.new_page(width=10, height=10)
    document.save(path)
    document.close()
    return path
