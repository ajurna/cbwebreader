import comic.api.mutations
import comic.api.queries
import graphene


class Query(comic.api.queries.Query, graphene.ObjectType):
    pass


class Mutation(comic.api.mutations.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
