"""
Test for the post images API.
"""
import tempfile

from PIL import Image
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import PostImage
from .test_posts_api import create_user, create_post

POST_IMAGES_URL = reverse('posts:postimage-list')


def detail_url(post_image_id):
    """Create and return post image detail URL."""
    return reverse('posts:postimage-detail', args=[post_image_id])


class PublicPostImagesAPITests(TestCase):
    """Test for API calls without authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=False)
        self.client.force_authenticate(self.user)
        self.post = create_post(self.user)

    def test_create_post_image_no_auth_not_allowed(self):
        """Test that creating a post image without being a staff
           raises an error."""
        payload = {
            'title': 'image title',
            'post': self.post.id
        }
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload['image'] = image_file
            res = self.client.post(POST_IMAGES_URL, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_post_image_no_auth_not_allowed(self):
        """Test that updating a post image without being a staff
           raises an error."""
        post_image = PostImage.objects.create(post=self.post, title='title')
        url = detail_url(post_image.id)
        payload = {'title': 'new image title'}

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post_image_no_auth_not_allowed(self):
        """Test that deleting a post image without being a staff
           raises an error."""
        post_image = PostImage.objects.create(post=self.post, title='title')
        url = detail_url(post_image.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class StaffPostImagesAPITests(TestCase):
    """Test for API calls that require is_staff set to True."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=True)
        self.client.force_authenticate(self.user)
        self.post = create_post(self.user)
        self.post_image = PostImage.objects.create(post=self.post, title='title')

    def test_create_post_image_success(self):
        """Test that creating a post image is successful."""
        payload = {
            'title': 'image title',
            'post': self.post.id
        }
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload['image'] = image_file
            res = self.client.post(POST_IMAGES_URL, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('image', res.data)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(res.data['post'], payload['post'])

    def test_update_post_image_success(self):
        """Test that updating a post image is successful."""
        url = detail_url(self.post_image.id)
        payload = {'title': 'new image title'}

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(res.data['post'], self.post_image.post.id)

    def test_delete_post_image_success(self):
        """Test that deleting a post image is successful."""
        url = detail_url(self.post_image.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        image_exists = PostImage.objects.filter(id=self.post_image.id).exists()
        self.assertFalse(image_exists)
