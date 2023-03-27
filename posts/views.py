"""
Views for the posts APIs.
"""
from drf_spectacular.utils import (extend_schema_view,
                                   extend_schema,
                                   OpenApiParameter,
                                   OpenApiTypes)
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import (IsAdminUser,
                                        IsAuthenticated,
                                        BasePermission,
                                        SAFE_METHODS)
from rest_framework.response import Response

from core.models import Post, Tag, Comment, PostImage, Vote
from posts import serializers


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma-separated list of tag IDs to filter.',
            ),
            OpenApiParameter(
                'sort',
                OpenApiTypes.STR,
                description='Sorting posts by: title, comments, date and update'
                            '(each with -asc or -desc)',
            )
        ]
    )
)
class PostsViewSet(viewsets.ModelViewSet):
    """Manage posts APIs. Unauthenticated users can only use
       GET method, to create, update and delete is_staff
       set to True is required."""
    serializer_class = serializers.PostSerializer
    queryset = Post.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser | ReadOnly]

    @staticmethod
    def _params_to_ints(qs):
        """Convert a list of string IDs to a list of integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Return post objects with optional filtering by tags and/ or sorting."""
        queryset = self.queryset
        tags = self.request.query_params.get('tags')
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        sort = self.request.query_params.get('sort')
        if sort:
            queryset = list(queryset)
            if sort == 'title-asc':
                queryset.sort(key=lambda p: p.title.lower())
            elif sort == 'title-desc':
                queryset.sort(key=lambda p: p.title.lower(), reverse=True)
            elif sort == 'comments-asc':
                queryset.sort(key=lambda p: p.number_of_comments)
            elif sort == 'comments-desc':
                queryset.sort(key=lambda p: p.number_of_comments, reverse=True)
            elif sort == 'date-asc':
                queryset.sort(key=lambda p: p.created_at)
            elif sort == 'date-desc':
                queryset.sort(key=lambda p: p.created_at, reverse=True)
            elif sort == 'update-asc':
                queryset.sort(key=lambda p: p.updated_at)
            elif sort == 'update-desc':
                queryset.sort(key=lambda p: p.updated_at, reverse=True)

        return queryset

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PostSerializer
        return serializers.PostDetailSerializer

    def perform_create(self, serializer):
        """Create a new post."""
        serializer.save(author=self.request.user)


class TagViewSet(mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """Manage tags in the database"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser | ReadOnly]
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class CommentViewSer(mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """Manage comments APIs. Auth is required to create, update and delete."""
    serializer_class = serializers.CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()

    def partial_update(self, request, *args, **kwargs):
        comment = self.get_object()

        # Check if the user is the author of the comment
        if comment.author != request.user:
            return Response({'detail': 'You are not the author of this comment.'}, status=status.HTTP_403_FORBIDDEN)

        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()

        # Check if the user is the author of the comment
        if comment.author != request.user:
            return Response({'detail': 'You are not the author of this comment.'}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Create a new comment."""
        serializer.save(author=self.request.user)


class PostImageViewSet(mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    """Manage post images APIs, is_staff set to True is required
       to create, update and delete."""
    serializer_class = serializers.PostImageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]
    queryset = PostImage.objects.all()


class VoteViewSet(mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """Manage vote APIs, only authenticated users can create,
       users are allowed to delete only their votes."""
    serializer_class = serializers.VoteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Vote.objects.all()

    def destroy(self, request, *args, **kwargs):
        vote = self.get_object()

        # Check if the user is the author of the comment
        if vote.user != request.user:
            return Response({'detail': 'You are not the author of this vote.'}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Create a new vote."""
        serializer.save(user=self.request.user)
