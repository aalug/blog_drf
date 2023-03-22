"""
Test for the comments API.
"""
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Comment
from .test_posts_api import create_user, create_post

COMMENTS_URL = reverse('posts:comment-list')


def detail_url(comment_id):
    """Create and return comment detail URL"""
    return reverse('posts:comment-detail', args=[comment_id])


def create_comment(author, post_id, text='Test text'):
    """Create and return a comment."""
    return Comment.objects.create(
        author=author,
        post=post_id,
        text=text
    )


class PublicCommentsAPITests(TestCase):
    """Test for API calls without authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=True)
        self.post = create_post(self.user)

    def test_create_comment_without_auth_error(self):
        """Test that trying to create a comment without auth raises an error."""
        payload = {
            'text': 'test comment',
            'post': self.post.id
        }
        res = self.client.post(COMMENTS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_comment_no_auth__not_allowed(self):
        """Test that updating a comment without authentication is not allowed."""
        comment = create_comment(self.user, self.post)
        url = detail_url(comment.id)

        res = self.client.patch(url, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_comment_no_auth__not_allowed(self):
        """Test that deleting a comment without authentication is not allowed."""
        comment = create_comment(self.user, self.post)
        url = detail_url(comment.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateCommentsAPITests(TestCase):
    """Test for API calls that require authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=False)
        self.client.force_authenticate(self.user)
        self.post = create_post(self.user)

    def test_create_comment_success(self):
        """Test creating a comment is successful."""
        payload = {
            'text': 'some comment text',
            'post': self.post.id
        }

        res = self.client.post(COMMENTS_URL, payload, format='json')

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        comment_exists = Comment.objects.filter(author=self.user, text=payload['text'])
        self.assertTrue(comment_exists)

    def test_update_comment_success(self):
        """Test updating a comment is successful."""
        comment = create_comment(self.user, self.post, 'text')
        url = detail_url(comment.id)
        payload = {'text': 'new comment text'}

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['text'], payload['text'])

    def test_delete_comment_success(self):
        """Test deleting a comment is successful."""
        comment = create_comment(self.user, self.post, 'text')
        url = detail_url(comment.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        comment_exists = Comment.objects.filter(id=comment.id).exists()
        self.assertFalse(comment_exists)

    def test_update_others_comments_not_allowed(self):
        """Test updating other users comments is not allowed."""
        other_user = create_user(
            is_staff=False,
            email='other@example.com',
            username='other'
        )
        comment = create_comment(other_user, self.post)

        url = detail_url(comment.id)
        res = self.client.patch(url, {})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_others_comments_not_allowed(self):
        """Test deleting other users comments is not allowed."""
        other_user = create_user(
            is_staff=False,
            email='other@example.com',
            username='other'
        )
        comment = create_comment(other_user, self.post)

        url = detail_url(comment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)



