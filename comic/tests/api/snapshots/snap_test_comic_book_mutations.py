# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestComicBookMutations::test_create_comic_books 1'] = {
    'data': {
        'createComicBook': {
            'comicBook': {
                'dateAdded': '2019-01-01T12:00:01+00:00',
                'fileName': 'test1.rar',
                'id': '2',
                'version': 1
            },
            'ok': True
        }
    }
}
