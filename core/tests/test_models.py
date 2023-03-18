"""
Test fpr models.
"""
import datetime

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.text import slugify

from core.models import Post, Comment, PostImage, Tag, image_file_path


def create_user(user_details: dict[str, str] = None):
    """Create and return a new user."""
    payload = {
        'email': 'user@example.com',
        'password': 'password123',
        'first_name': 'First',
        'date_of_birth': '1950-10-10'
    }
    if user_details is not None:
        payload.update(user_details)
    return get_user_model().objects.create_user(payload)


def create_sample_post(user, details=None):
    """Create and return a sample post."""
    payload = {
        'title': 'Test Post',
        'author': user,
        'description': 'Test post description',
        'body': 'Test post body',
        'cover_image': 'path/to/image.jpg'
    }
    if details is not None:
        payload.update(details)
    return Post.objects.create(**payload)


class UserModelTests(TestCase):
    """Test for the User model."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'test123'
        first_name = 'John'
        date_of_birth = datetime.datetime(day=1, month=1, year=2011)
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            date_of_birth=date_of_birth
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='password123',
                first_name='Adam',
                date_of_birth='2012-12-12'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='password123',
                first_name='Marc',
                date_of_birth='2012-12-12'
            )

    def test_new_user_with_too_short_password_raise_error(self):
        """Test that creating a user without a password raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='testUser5@example.com',
                password='test1',
                first_name='Carl',
                date_of_birth='2012-12-12'
            )

    def test_new_user_with_6_chars_password_success(self):
        """Test that creating a user with a password 6 characters
           does not raise a ValueError."""
        get_user_model().objects.create_user(
            email='testUser6@example.com',
            password='test12',
            first_name='Joe',
            date_of_birth='2012-12-12'
        )
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='admin123',
            first_name='Admin',
            date_of_birth='1999-09-09'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class PostModelTests(TestCase):
    """Tests for the models connected to the Post model."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='userr@example.com',
            password='test123',
            first_name='Joe',
            date_of_birth='2000-12-12'
        )
        self.post = create_sample_post(self.user)

    def test_create_post(self):
        """Test creating a post is successful."""
        post = create_sample_post(self.user, {'title': 'Some title'})
        self.assertEqual(str(post), post.title)

    def test_slug_is_correct(self):
        """Test slug is created correctly."""
        title = 'Post title'
        p = create_sample_post(self.user, {'title': title})
        post = Post.objects.filter(title=title).first()
        expected_slug = slugify(title)
        self.assertEquals(expected_slug, post.slug)

    def test_create_tag(self):
        """Test creating a tag is successful."""
        tag = Tag.objects.create(
            user=self.user,
            name='Tag1'
        )

        self.assertEqual(str(tag), tag.name)

    @patch('core.models.uuid.uuid4')
    def test_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = image_file_path(None, 'image.jpg')

        self.assertEqual(file_path, f'uploads/post/{uuid}.jpg')

    def test_create_post_image(self):
        """Test creating a post image is successful."""
        post_image = PostImage.objects.create(
            post=self.post,
            title='image title',
            image='path/to/image.jpg'
        )

        self.assertEqual(str(post_image), post_image.title)

    def test_posts_images_property(self):
        """Test images property of the Post model."""
        post_image = PostImage.objects.create(
            post=self.post,
            title='image title',
            image='path/to/image.jpg'
        )

        self.assertIn(post_image, self.post.images)
        self.assertEqual(self.post.images[0], post_image)

    def test_create_comment_is_successful(self):
        """Test creating a comment is successful."""
        comment = Comment.objects.create(
            text='some comment',
            author=self.user,
            post=self.post,
        )

        self.assertEqual(str(comment), f'{comment.author}: {comment.text[:20]}')

    def test_posts_comments_property(self):
        """Test comments property of the Post model."""
        comment = Comment.objects.create(
            text='some comment',
            author=self.user,
            post=self.post,
        )

        self.assertIn(comment, self.post.comments)
        self.assertEqual(self.post.comments[0], comment)
