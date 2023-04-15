"""
Tests for the votes API.
"""
from django.urls import reverse
from django.test import TestCase, TransactionTestCase
from django.test.signals import setting_changed

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Vote
from .test_posts_api import create_user, create_post
from .test_comments_api import create_comment

VOTES_URL = reverse('posts:vote-list')


def detail_url(vote_id):
    """Create and return vote detail URL."""
    return reverse('posts:vote-detail', args=[vote_id])


def create_vote(user, comment, vote_type='upvote'):
    """Create and return a vote."""
    return Vote.objects.create(
        user=user,
        comment=comment,
        vote_type=vote_type
    )


class PublicVotesAPITests(TestCase):
    """Test for API calls without authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=True)
        self.post = create_post(self.user)
        self.comment = create_comment(self.user, self.post)

    def test_no_auth_create_vote_not_allowed(self):
        """Test that voting is not allowed without authentication."""
        payload_1 = {
            'comment': self.comment.id,
            'vote_type': Vote.UPVOTE
        }
        payload_2 = {
            'comment': self.comment.id,
            'vote_type': Vote.DOWNVOTE
        }
        res_1 = self.client.post(VOTES_URL, payload_1, format='json')
        res_2 = self.client.post(VOTES_URL, payload_2, format='json')

        self.assertEqual(res_1.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_auth_delete_vote_not_allowed(self):
        """Test that deleting a vote is not allowed without authentication."""
        vote = create_vote(self.user, self.comment)
        url = detail_url(vote.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateVotesAPITests(TestCase):
    """Test for API calls that require authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=False)
        self.client.force_authenticate(self.user)
        self.post = create_post(self.user)
        self.comment = create_comment(self.user, self.post)

    def test_add_upvote(self):
        """Test that adding an upvote is successful."""
        payload = {
            'comment': self.comment.id,
            'vote_type': Vote.UPVOTE
        }
        res = self.client.post(VOTES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.all().count(), 1)
        self.assertEqual(res.data['vote_type'], payload['vote_type'])
        self.assertEqual(res.data['comment'], payload['comment'])
        self.assertEqual(res.data['user'], self.user.id)

    def test_add_downvote(self):
        """Test that adding a downvote is successful."""
        payload = {
            'comment': self.comment.id,
            'vote_type': Vote.DOWNVOTE
        }
        res = self.client.post(VOTES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.all().count(), 1)
        self.assertEqual(res.data['vote_type'], payload['vote_type'])
        self.assertEqual(res.data['comment'], payload['comment'])
        self.assertEqual(res.data['user'], self.user.id)

    def test_delete_upvote(self):
        """Test that deleting an upvote is successful."""
        vote = create_vote(self.user, self.comment)
        url = detail_url(vote.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        vote_exists = Vote.objects.filter(id=vote.id).exists()
        self.assertFalse(vote_exists)

    def test_delete_downvote(self):
        """Test that deleting a downvote is successful."""
        vote = create_vote(self.user, self.comment, Vote.DOWNVOTE)
        url = detail_url(vote.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        vote_exists = Vote.objects.filter(id=vote.id).exists()
        self.assertFalse(vote_exists)

    def test_deleting_others_votes_not_allowed(self):
        """Test that deleting other users votes is not allowed."""
        other_user = create_user(
            is_staff=False,
            email='other@example.com',
            username='other'
        )
        vote = create_vote(other_user, self.comment)
        url = detail_url(vote.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        vote_exists = Vote.objects.filter(id=vote.id).first()
        self.assertTrue(vote_exists)

    def test_double_upvote(self):
        """Test that voting up twice will result in 0 votes."""
        payload = {
            'comment': self.comment.id,
            'vote_type': Vote.UPVOTE
        }
        res_1 = self.client.post(VOTES_URL, payload, format='json')
        res_2 = self.client.post(VOTES_URL, payload, format='json')

        self.assertEqual(res_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_2.status_code, status.HTTP_201_CREATED)
        self.assertFalse(
            Vote.objects.filter(comment=self.comment, user=self.user).exists()
        )

    def test_double_downvote(self):
        """Test that voting down twice will result in 0 votes."""
        payload = {
            'comment': self.comment.id,
            'vote_type': Vote.DOWNVOTE
        }
        res_1 = self.client.post(VOTES_URL, payload, format='json')
        res_2 = self.client.post(VOTES_URL, payload, format='json')

        self.assertEqual(res_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_2.status_code, status.HTTP_201_CREATED)
        self.assertFalse(
            Vote.objects.filter(comment=self.comment, user=self.user).exists()
        )
