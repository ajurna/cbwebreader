import graphene
from comic.models import ComicBook, Directory
from graphene_django import DjangoObjectType


class ComicBookType(DjangoObjectType):
    class Meta:
        model = ComicBook


class DirectoryType(DjangoObjectType):
    class Meta:
        model = Directory


class DirectoryInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    parent = graphene.String()
    selector = graphene.UUID()


class ComicBookInput(graphene.InputObjectType):
    id = graphene.Int()
    file_name = graphene.String()
    date_added = graphene.String()
    directory = graphene.List(DirectoryInput)
    selector = graphene.UUID()
    version = graphene.Int()
