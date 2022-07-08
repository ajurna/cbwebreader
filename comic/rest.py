from uuid import UUID

from django.contrib.auth.models import User, Group
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from comic import models
from rest_framework import viewsets, serializers, mixins, permissions


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class DirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Directory

        fields = ['name', 'parent', 'selector', 'thumbnail', 'thumbnail_issue', 'thumbnail_index', 'classification']


class DirectoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows Directories to be viewed.
    """
    queryset = models.Directory.objects.all()
    lookup_field = 'selector'
    serializer_class = DirectorySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def listing(self, request, selector: UUID):
        directories = models.Directory.objects.filter(parent=selector)
        serializer = self.get_serializer(directories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def base(self, request):
        directories = models.Directory.objects.filter(parent__isnull=True)
        serializer = self.get_serializer(directories, many=True)
        return Response(serializer.data)


class ComicBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ComicBook
        fields = ['file_name', 'date_added', 'directory', 'selector', 'version', 'thumbnail', 'thumbnail_index']


class ComicBookViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = models.ComicBook.objects.all()
    serializer_class = ComicBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['directory', 'selector']
