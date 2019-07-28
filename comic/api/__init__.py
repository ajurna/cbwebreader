import graphene

from comic.api.mutations import Mutation
from comic.api.queries import Query

schema = graphene.Schema(query=Query, mutation=Mutation, types=[])
