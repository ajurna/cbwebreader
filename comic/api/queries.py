import graphene

from comic.api.types import ComicBookInput, ComicBookType, DirectoryInput, DirectoryType
from comic.models import ComicBook, Directory


class Query(graphene.ObjectType):
    comic_book = graphene.Field(ComicBookType, id=graphene.Int())
    directory = graphene.Field(DirectoryType, id=graphene.Int())
    comic_books = graphene.List(ComicBookType)
    directorys = graphene.List(DirectoryType)

    def resolve_comic_book(self, info, **kwargs):
        id = kwargs.get("id")

        if id is not None:
            return ComicBook.objects.get(pk=id)

        return None

    def resolve_dictory(self, info, **kwargs):
        id = kwargs.get("id")

        if id is not None:
            return Directory.objects.get(pk=id)

        return None

    def resolve_comic_books(self, info, **kwargs):
        return ComicBook.objects.all()

    def resolve_directorys(self, info, **kwargs):
        return Directory.objects.all()
