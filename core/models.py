"""
Database models.
"""
import uuid
import os

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.utils.text import slugify


def image_file_path(instance, filename):
    """Generate file path for new image"""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'post', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        if len(password) < 6:
            raise ValueError('Password must be at least 6 characters.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and return a new superuser."""
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """User profile for the User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    points = models.PositiveIntegerField(default=0)
    profile_image = models.ImageField(upload_to=image_file_path, null=True)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    """Post table."""
    title = models.CharField(max_length=240, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    description = models.CharField(max_length=255)
    body = models.TextField()
    cover_image = models.ImageField(upload_to=image_file_path, blank=False, null=False)
    tags = models.ManyToManyField('Tag')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at', '-updated_at']

    @property
    def comments(self):
        """Return comments for this post."""
        return Comment.objects.filter(post=self)

    @property
    def images(self):
        """Return images for this post."""
        return PostImage.objects.filter(post=self)

    def save(self, *args, **kwargs):
        """Create a slug for this post before saving it."""
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class PostImage(models.Model):
    """Image for a Post."""
    title = models.CharField(max_length=100)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=image_file_path)

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comment to a post."""
    text = models.TextField(max_length=1000)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.author}: {self.text[:20]}'

    class Meta:
        ordering = ['-created_at', '-updated_at']


class Tag(models.Model):
    """Tag for filtering posts."""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name


# self.assertEqual(user.date_of_birth.strftime('%Y-%m-%d'), SAMPLE_USER_DETAILS['date_of_birth'])
