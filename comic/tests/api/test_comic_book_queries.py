import os

from freezegun import freeze_time
from graphene.test import Client
from snapshottest.django import TestCase

from comic.api.schema import schema
from comic.models import ComicBook, Setting


class TestComicBookQueries(TestCase):
    @freeze_time("2019-01-01 12:00:01")
    def setUp(self, **kwargs):
        # TODO: refactor test setup to avoid using files on disk for faster tests
        Setting.objects.create(name="BASE_DIR", value=os.path.join(os.getcwd(), "comic", "test"))
        ComicBook.process_comic_book("test1.rar")

    @freeze_time("2019-01-01 12:00:01")
    def test_get_comic_books(self):
        get_comic_books = """
                query GET_ALL_COMIC_BOOKS {
                    comicBooks {
                        id
                        fileName
                        dateAdded
                        version
                        directory {
                            id
                            name
                        }
                    }
                }
            """

        client = Client(schema)
        executed = client.execute(get_comic_books)

        self.assertMatchSnapshot(executed)
