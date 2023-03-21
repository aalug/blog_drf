"""
Tests for signals in posts app.
"""
from django.test import TestCase
from core.models import Post, Tag
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
