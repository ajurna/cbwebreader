# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestComicBookQueries::test_get_comic_books 1'] = {
    'data': {
        'comicBooks': [
            {
                'dateAdded': '2019-01-01T12:00:01+00:00',
                'directory': None,
                'fileName': 'test1.rar',
                'id': '1',
                'version': 1
            }
        ]
    }
}
