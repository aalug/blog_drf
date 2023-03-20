"""
Serializers for the posts API.
"""
from rest_framework import serializers

from core.models import Post, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        extra_kwargs = {'id': {'read_only': True}}


class PostSerializer(serializers.ModelSerializer):
    """Serializer for the post model."""
    tags = TagSerializer(many=True, required=False)

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

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ('body', 'images', 'comments')