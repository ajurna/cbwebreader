import graphene

from comic.models import ComicBook, Directory
from comic.api.types import ComicBookInput, ComicBookType, DirectoryInput, DirectoryType


class CreateDirectory(graphene.Mutation):
    class Arguments:
        input = DirectoryInput(required=True)

    ok = graphene.Boolean()
    directory = graphene.Field(DirectoryType)

    @staticmethod
    def mutate(root, info, input=None):
        ok = True
        directory = Directory(name=input.name)
        directory.save()

        return CreateDirectory(ok=ok, directory=directory)


class UpdateDirectory(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        input = DirectoryInput(required=True)

    ok = graphene.Boolean()
    directory = graphene.Field(DirectoryType)

    @staticmethod
    def mutate(root, info, id, input=None):
        ok = False
        directory = Directory.objects.get(pk=id)
        if directory:
            ok = True
            directory.name = input.name
            directory.save()
            return UpdateDirectory(ok=ok, directory=directory)
        return UpdateDirectory(ok=ok, directory=None)


class CreateComicBook(graphene.Mutation):
    class Arguments:
        input = ComicBookInput(required=True)

    ok = graphene.Boolean()
    comic_book = graphene.Field(ComicBookType)

    @staticmethod
    def mutate(root, info, input=None):
        ok = True
        directory = None

        if input.directory:
            directory = Directory.objects.get(pk=input.directory[0].id)

        comic_book = ComicBook(file_name=input.file_name, directory=directory)
        comic_book.save()

        return CreateComicBook(ok=ok, comic_book=comic_book)


class UpdateComicBook(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        input = ComicBookInput(required=True)

    ok = graphene.Boolean()
    comic_book = graphene.Field(ComicBookType)

    @staticmethod
    def mutate(root, info, id, input=None):
        ok = False
        comic_book = ComicBook.objects.get(pk=id)
        if comic_book:
            ok = True
            directory = None

            if input.directory:
                directory = Directory.objects.get(pk=input.directory[0].id)
                if directory is None:
                    return UpdateComicBook(ok=False, comic_book=None)

            comic_book.file_name = input.file_name
            comic_book.directory = input.directory

            return UpdateComicBook(ok=ok, comic_book=comic_book)
        return UpdateComicBook(ok=ok, comic_book=None)


class Mutation(graphene.ObjectType):
    create_comic_book = CreateComicBook.Field()
    create_directory = CreateDirectory.Field()
    update_comic_book = UpdateComicBook.Field()
    update_directory = UpdateDirectory.Field()
