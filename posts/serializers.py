"""
Serializers for the posts API.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import Post, Tag, Comment, PostImage, Vote, UserProfile


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        extra_kwargs = {'id': {'read_only': True}}


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
        fields = ('id', 'email', 'username', 'is_staff')


class UserProfileSerializer(serializers.ModelSerializer):
    """serializer for the UserProfile model."""

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name',
                  'date_of_birth', 'profile_image', 'points')


class PublicUserSerializer(UserSerializer):
    """Serializer for the user model. Used for comments
       so the other users can see specific data."""
    user_profile = UserProfileSerializer()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('user_profile',)


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for adding comment to a post."""

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'post', 'created_at')
        extra_kwargs = {
            'post': {'required': True, 'write_only': True},
            'text': {'required': True},
            'author': {'read_only': True},
            'created_at': {'read_only': True},
        }


class GetCommentSerializer(CommentSerializer):
    """Serializer for fetching comments. It extends CommentSerializer,
       and adds additional fields needed only for GET method."""
    author = PublicUserSerializer()
    has_voted = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ('number_of_upvotes',
                                                  'number_of_downvotes',
                                                  'created_at',
                                                  'updated_at',
                                                  'has_voted')
        read_only = True

    def get_has_voted(self, obj):
        user = self.context['request'].user

        if user.is_anonymous:
            return None

        # Check if the user has voted on the comment
        try:
            vote = Vote.objects.get(user=user, comment=obj.id)
            return vote.vote_type
        except Vote.DoesNotExist:
            return None


class PostSerializer(serializers.ModelSerializer):
    """Serializer for the post model."""
    tags = TagSerializer(many=True, required=False)
    author = UserSerializer(required=False)

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


class PostDetailSerializer(PostSerializer):
    """Serialize a post details."""
    comments = GetCommentSerializer(many=True, required=False)
    images = PostImageSerializer(many=True, required=False)

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ('body', 'images', 'comments')
        extra_kwargs = PostSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({
            'comments': {'read_only': True},
            'images': {'read_only': True},
        })

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

    def create(self, validated_data):
        """Create a new vote."""
        # Get the current user from the request object
        user = self.context['request'].user

        comment_id = validated_data.get('comment').id
        vote = Vote.objects.filter(user=user, comment__id=comment_id).first()

        if not vote:
            # User has not voted for this comment yet, proceed normally
            return Vote.objects.create(**validated_data)

        # User has voted for this comment before, so check if the vote type is the same
        if vote.vote_type == validated_data.get('vote_type'):
            # Vote type is the same, so delete the existing vote
            vote.delete()
        else:
            # Vote type is different, so update the existing vote
            vote.delete()
            return Vote.objects.create(**validated_data)
        return vote
