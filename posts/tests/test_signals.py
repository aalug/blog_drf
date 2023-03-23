"""
Tests for signals in posts app.
"""
from django.test import TestCase
from core.models import Post, Tag, Comment, Vote, UserProfile
from .test_posts_api import create_post, create_user


class DeleteRelatedTagsSignalTest(TestCase):
    """Tests for the delete related tags signal."""

    def setUp(self):
        # create a Post and two Tags
        self.user = create_user(is_staff=True)
        self.post = create_post(self.user)
        self.tag1 = Tag.objects.create(name='Tag 1')
        self.tag2 = Tag.objects.create(name='Tag 2')
        # Connect the tags to the post
        self.post.tags.add(self.tag1, self.tag2)

    def test_delete_related_tags(self):
        """Test deleting related tags is successful."""
        self.post.delete()

        self.assertFalse(Tag.objects.filter(name=self.tag1.name).exists())
        self.assertFalse(Tag.objects.filter(name=self.tag2.name).exists())

    def test_delete_related_tags_with_other_post(self):
        """Test that tag will not be deleted if it's related to another post."""
        other_post = create_post(self.user, title='other post')
        other_post.tags.add(self.tag1)
        # delete the first post
        self.post.delete()

        # assert that only one tag is deleted
        self.assertTrue(Tag.objects.filter(name=self.tag1.name).exists())
        self.assertFalse(Tag.objects.filter(name=self.tag2.name).exists())
        self.assertEqual(len(self.tag1.post_set.all()), 1)


class CalculateUsersPointsSignalsTest(TestCase):
    """Tests for the calculate user points signals."""

    def setUp(self):
        self.comment_author = create_user(
            is_staff=False,
            email='author@example.com',
            username='author'
        )
        self.post = create_post(self.comment_author)
        self.comment = Comment.objects.create(
            text='test comment',
            author=self.comment_author,
            post=self.post
        )
        self.user = create_user(is_staff=False)

    def test_user_points_add_upvote(self):
        """Test that after upvote, user's points increase."""
        points_before_vote = UserProfile.objects.get(user=self.comment_author).points

        vote = Vote.objects.create(
            user=self.user,
            comment=self.comment,
            vote_type=Vote.UPVOTE
        )
        points_after_vote = UserProfile.objects.get(user=self.comment_author).points

        self.assertEqual(points_before_vote + 1, points_after_vote)

    def test_user_points_add_downvote(self):
        """Test that after downvote, user's points decrease."""
        points_before_vote = UserProfile.objects.get(user=self.comment_author).points

        vote = Vote.objects.create(
            user=self.user,
            comment=self.comment,
            vote_type=Vote.DOWNVOTE
        )
        points_after_vote = UserProfile.objects.get(user=self.comment_author).points

        self.assertEqual(points_before_vote - 1, points_after_vote)

    def test_user_points_delete_upvote(self):
        """Test that after deleting an upvote, user's points decrease."""
        points_before_vote = UserProfile.objects.get(user=self.comment_author).points

        vote = Vote.objects.create(
            user=self.user,
            comment=self.comment,
            vote_type=Vote.UPVOTE
        )
        points_after_vote = UserProfile.objects.get(user=self.comment_author).points

        self.assertEqual(points_before_vote + 1, points_after_vote)
        vote.delete()
        points_after_vote_delete = UserProfile.objects.get(user=self.comment_author).points
        self.assertEqual(points_before_vote, points_after_vote_delete)

    def test_user_points_delete_downvote(self):
        """Test that after deleting a downvote, user's points increase."""
        points_before_vote = UserProfile.objects.get(user=self.comment_author).points

        vote = Vote.objects.create(
            user=self.user,
            comment=self.comment,
            vote_type=Vote.DOWNVOTE
        )
        points_after_vote = UserProfile.objects.get(user=self.comment_author).points

        self.assertEqual(points_before_vote - 1, points_after_vote)
        vote.delete()
        points_after_vote_delete = UserProfile.objects.get(user=self.comment_author).points
        self.assertEqual(points_before_vote, points_after_vote_delete)
