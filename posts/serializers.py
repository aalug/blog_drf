"""
Serializers for the posts API.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Post, Tag, Comment, PostImage, Vote


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        extra_kwargs = {'id': {'read_only': True}}


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for adding comment to a post."""

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'post',
                  'number_of_upvotes', 'number_of_downvotes',
                  'created_at', 'updated_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'author': {'read_only': True},
            'post': {'required': True},
            'text': {'required': True},
            'number_of_upvotes': {'read_only': True},
            'number_of_downvotes': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }


class PostImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to a post."""

    class Meta:
        model = PostImage
        fields = ('id', 'title', 'post', 'image')
        extra_kwargs = {
            'image': {'required': True},
            'post': {'required': True},
            'title': {'required': True, 'max_length': 100}
        }


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""

    class Meta:
        model = get_user_model()
        fields = ['id', 'email', 'username', 'is_staff']


class PostSerializer(serializers.ModelSerializer):
    """Serializer for the post model."""
    tags = TagSerializer(many=True, required=False)
    author = UserSerializer()

    class Meta:
        model = Post
        fields = ('id', 'title', 'slug', 'author',
                  'description', 'tags', 'cover_image',
                  'number_of_comments', 'created_at',
                  'updated_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'author': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'number_of_comments': {'read_only': True},
        }

    @staticmethod
    def _get_or_create_tags(tags, post):
        """Handle getting or creating tags as needed."""
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                **tag
            )
            post.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a new recipe."""
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        self._get_or_create_tags(tags, post)
        return post

    def update(self, instance, validated_data):
        """Update a post."""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PostDetailSerializer(PostSerializer):
    """Serialize a post detail view."""
    comments = CommentSerializer(many=True, required=False)
    images = PostImageSerializer(many=True, required=False)

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ('body', 'images', 'comments')


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for the vote model."""
    vote_type = serializers.ChoiceField(choices=Vote.VOTE_CHOICES)

    class Meta:
        model = Vote
        fields = ('id', 'user', 'comment', 'vote_type')
        extra_kwargs = {
            'id': {'read_only': True},
            'user': {'read_only': True}
        }
