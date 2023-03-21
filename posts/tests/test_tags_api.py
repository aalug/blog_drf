"""
Tests for the tags API.
"""
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from .test_posts_api import create_post, create_user

TAGS_URL = reverse('posts:tag-list')
POSTS_URL = reverse('posts:post-list')


def detail_url(tag_id):
    """Create and return tag details url."""
    return reverse('posts:tag-detail', args=[tag_id])


def create_tag(name='test tag'):
    """Create and return a new tag."""
    return Tag.objects.create(name=name)


class PublicTagsAPITests(TestCase):
    """TEst unauthenticated tag API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_all_tags(self):
        """Test retrieving all tags without auth is successful."""
        tag = create_tag()
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data['results']
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], tag.id)
        self.assertEqual(results[0]['name'], tag.name)

    def test_retrieve_tag_details_error(self):
        """Test retrieving tag details raises error."""
        tag = create_tag()
        url = detail_url(tag.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_auth_required_to_post(self):
        """Test that authentication is required to make
           POST request to tags endpoint."""
        res = self.client.post(TAGS_URL, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_to_patch(self):
        """Test that authentication is required to make
           PATCH request to tag-details endpoint."""
        tag = create_tag()
        url = detail_url(tag.id)
        res = self.client.patch(url, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_to_delete(self):
        """Test that authentication is required to make
           DELETE request to tag-details endpoint."""
        tag = create_tag()
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class StaffTagsAPITests(TestCase):
    """Test for API calls that require is_staff set to True."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(is_staff=True)
        self.client.force_authenticate(self.admin)

    def test_update_tag_success(self):
        """Test updating a tag is successful."""
        tag = create_tag(name='foo')
        payload = {'name': 'bar'}
        url = detail_url(tag.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(res.data['name'], payload['name'])
        edited_tag = Tag.objects.filter(id=tag.id).first()
        self.assertEqual(edited_tag.name, payload['name'])

    def test_delete_tag_success(self):
        """Test deleting a tag is successful."""
        tag = create_tag()
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tag_exists = Tag.objects.filter(id=tag.id).exists()
        self.assertFalse(tag_exists)

    def test_filter_tags_assigned_to_post(self):
        """Test listing tags by those assigned to a post."""
        tag_1 = create_tag(name='tag 1')
        create_tag(name='tag 2')
        post = create_post(user=self.admin)
        post.tags.add(tag_1)

        res = self.client.get(POSTS_URL)
        post_data = res.data['results'][0]

        self.assertEqual(len(post_data['tags']), 1)
        self.assertEqual(post_data['tags'][0]['id'], tag_1.id)
        self.assertEqual(post_data['tags'][0]['name'], tag_1.name)
