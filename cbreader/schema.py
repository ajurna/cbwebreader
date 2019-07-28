import graphene

import comic.api.schema


class Query(comic.api.schema.Query, graphene.ObjectType):
    pass


class Mutation(comic.api.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
