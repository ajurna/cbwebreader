import os

from graphene.test import Client
from snapshottest.django import TestCase
from freezegun import freeze_time

from comic.api.schema import schema
from comic.models import ComicBook, Directory, Setting


class TestComicBookMutations(TestCase):
    def setUp(self, **kwargs):
        # TODO: refactor test setup to avoid using files on disk for faster tests
        Setting.objects.create(name="BASE_DIR", value=os.path.join(os.getcwd(), "comic", "test"))
        ComicBook.process_comic_book("test1.rar")
        directory = Directory(name="/data/")
        directory.save()

    @freeze_time("2019-01-01 12:00:01")
    def test_create_comic_books(self):
        comic_book_input = {"fileName": "test1.rar", "directory": 1}
        create_comic_books = """
                mutation CREATE_COMIC_BOOK ($fileName: String!, $directory: ID!) {
                    createComicBook(input: {fileName: $fileName, directory: {id: $directory}}) {
                        ok
                        comicBook {
                            id
                            fileName
                            dateAdded
                            version
                        }
                    }
                }
            """

        client = Client(schema)
        executed = client.execute(create_comic_books, variables=comic_book_input)

        self.assertMatchSnapshot(executed)
