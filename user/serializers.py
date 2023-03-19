"""
Serializers for the user API.
"""
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _

from rest_framework import serializers, exceptions

from core.models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'username', 'password', 'created_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'password': {'write_only': True, 'min_length': 6},
            'created_at': {'read_only': True}
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile object. It can be used to create a user
       with UserProfile and to update password and all profile information."""
    user = UserSerializer(required=True)

    class Meta:
        model = UserProfile
        fields = (
            'user',
            'first_name',
            'last_name',
            'date_of_birth',
            'profile_image'
        )
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'date_of_birth': {'required': False},
            'profile_image': {'required': False}
        }

    def create(self, validated_data):
        """Create a new user with encrypted password and UserProfile."""
        user_data = validated_data.pop('user')

        # Create the user object
        user = get_user_model().objects.create_user(
            email=user_data['email'],
            username=user_data['username'],
            password=user_data['password']
        )

        # Create the user profile object
        profile = UserProfile.objects.create(
            user=user,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            date_of_birth=validated_data.get('date_of_birth', None),
            profile_image=validated_data.get('profile_image', None),
        )
        return profile

    def update(self, instance, validated_data):
        """Update a user with a new password and UserProfile data."""
        user_data = validated_data.pop('user', None)
        if user_data is not None:
            if 'email' in user_data:
                raise exceptions.ValidationError('Email field is not allowed to be updated.')
            if 'username' in user_data:
                raise exceptions.ValidationError('Username field is not allowed to be updated.')

            user = instance.user
            password = user_data.get('password', None)
            if password is not None:
                user.set_password(password)
            user.save()

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.save()

        return instance


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        required=True
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs
