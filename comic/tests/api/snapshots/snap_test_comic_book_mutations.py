# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestComicBookMutations::test_create_comic_books 1'] = {
    'data': {
        'createComicBook': None
    },
    'errors': [
        {
            'locations': [
                {
                    'column': 21,
                    'line': 3
                }
            ],
            'message': 'Directory matching query does not exist.',
            'path': [
                'createComicBook'
            ]
        }
    ]
}
