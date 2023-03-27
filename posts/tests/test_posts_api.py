"""
Test for the posts API.
"""
import tempfile
from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from django.utils.text import slugify

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Post, UserProfile, Comment, PostImage

POSTS_URL = reverse('posts:post-list')


def detail_url(post_id):
    """Create and return post detail URL"""
    return reverse('posts:post-detail', args=[post_id])


def create_user(is_staff, **params):
    """Create and return a new user."""
    default_details = {
        'email': 'user@example.com',
        'password': '123123',
        'username': 'user123'
    }
    default_details.update(params)
    user = get_user_model().objects.create_user(**default_details)
    if is_staff:
        user.is_staff = True
    UserProfile.objects.create(user=user)
    return user


def create_post(user, **params):
    """Create and return a post."""
    default_params = {
        'title': 'Test title',
        'description': 'Test post description',
        'body': 'Test post body',
    }
    default_params.update(params)
    return Post.objects.create(author=user, **default_params)


class PublicPostsAPITests(TestCase):
    """Test unauthenticated posts API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=True)
        self.post = create_post(self.user)

    def test_get_posts_success(self):
        """Test that retrieving a post list is successful without auth."""
        res = self.client.get(POSTS_URL)
        results = res.data['results']

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 1)
        self.assertEqual(res.data['count'], 1)
        self.assertIn('number_of_comments', results[0])

        # body should be only in post details
        self.assertNotIn('body', results[0])

    def test_auth_required_to_post(self):
        """Test that authentication is required to make
           POST requests to posts endpoint."""
        res = self.client.post(POSTS_URL, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_to_patch(self):
        """Test that authentication is required to make
           PATCH requests to post-details endpoint."""
        url = detail_url(self.post.id)
        res = self.client.patch(url, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_to_delete(self):
        """Test that authentication is required to make
           DELETE requests to post-details endpoint."""
        url = detail_url(self.post.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_post_details_success(self):
        """Test fetching post details is successful,
           and returns all fields"""
        url = detail_url(self.post.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], self.post.title)
        self.assertEqual(res.data['slug'], self.post.slug)
        self.assertEqual(res.data['author'], self.post.author.id)
        self.assertEqual(res.data['description'], self.post.description)
        self.assertEqual(res.data['body'], self.post.body)
        self.assertIn('images', res.data)
        self.assertIn('comments', res.data)
        self.assertIn('tags', res.data)

    def test_n_of_comments_field(self):
        """Test number_of_comments field returns correct value."""
        Comment.objects.create(
            text='some comment',
            author=self.user,
            post=self.post
        )
        res = self.client.get(POSTS_URL)
        post = res.data['results'][0]

        self.assertEqual(post['number_of_comments'], 1)

    def test_get_posts_comments(self):
        """Test that comments are returned with the post details."""
        comment = Comment.objects.create(
            text='comment test',
            post=self.post,
            author=self.user
        )
        url = detail_url(self.post.id)
        res = self.client.get(url)

        comments = res.data['comments']

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['author'], comment.author.id)
        self.assertEqual(comments[0]['text'], comment.text)

    def test_get_posts_images(self):
        """Test that post images are returned with the post details."""
        post_image = PostImage.objects.create(title='title', post=self.post)
        url = detail_url(self.post.id)
        res = self.client.get(url)

        images = res.data['images']

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['title'], post_image.title)


class SortPostsTests(TestCase):
    """Test for API calls that use sorting of posts."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(is_staff=True)
        self.post_1 = create_post(self.user, title='post 1')
        self.post_2 = create_post(self.user, title='post 2')

    def test_sorting_posts_by_comments(self):
        """Test sorting posts by comments in ascending and descending order."""
        Comment.objects.create(
            text='test comment',
            author=self.user,
            post=self.post_1
        )
        res_asc = self.client.get(POSTS_URL, {'sort': 'comments-asc'})
        results_asc = res_asc.data['results']

        self.assertGreater(
            results_asc[1]['number_of_comments'],
            results_asc[0]['number_of_comments']
        )

        res_desc = self.client.get(POSTS_URL, {'sort': 'comments-desc'})
        results_desc = res_desc.data['results']

        self.assertGreater(
            results_desc[0]['number_of_comments'],
            results_desc[1]['number_of_comments']
        )

    def tst_sorting_by_title(self):
        res_asc = self.client.get(POSTS_URL, {'sort': 'title-asc'})
        results_asc = res_asc.data['results']

        self.assertGreater(
            results_asc[1]['title'],
            results_asc[0]['title']
        )

        res_desc = self.client.get(POSTS_URL, {'sort': 'title-desc'})
        results_desc = res_desc.data['results']

        self.assertGreater(
            results_desc[0]['title'],
            results_desc[1]['title']
        )

    def tst_sorting_posts_by_date(self):
        """Test sorting posts by date (created_at)
           in ascending and descending order."""
        res_asc = self.client.get(POSTS_URL, {'sort': 'date-asc'})
        results_asc = res_asc.data['results']

        self.assertGreater(
            results_asc[1]['created_at'],
            results_asc[0]['created_at']
        )

        res_desc = self.client.get(POSTS_URL, {'sort': 'date-desc'})
        results_desc = res_desc.data['results']

        self.assertGreater(
            results_desc[0]['created_at'],
            results_desc[1]['created_at']
        )

    def tst_sorting_posts_by_update(self):
        """Test sorting posts by updated_at in ascending and descending order."""
        res_asc = self.client.get(POSTS_URL, {'sort': 'update-asc'})
        results_asc = res_asc.data['results']

        self.assertGreater(
            results_asc[1]['updated_at'],
            results_asc[0]['updated_at']
        )

        res_desc = self.client.get(POSTS_URL, {'sort': 'update-desc'})
        results_desc = res_desc.data['results']

        self.assertGreater(
            results_desc[0]['updated_at'],
            results_desc[1]['updated_at']
        )


class StaffPostsAPITests(TestCase):
    """Test for API calls that require is_staff set to True."""

    def setUp(self):
        self.client = APIClient()
        self.admin = create_user(is_staff=True)
        self.client.force_authenticate(self.admin)

    def test_create_post_success(self):
        """Test creating a post is successful."""
        payload = {
            'title': 'post',
            'description': 'post description',
            'body': 'body'
        }
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload['cover_image'] = image_file
            res = self.client.post(POSTS_URL, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(res.data['description'], payload['description'])
        self.assertEqual(res.data['author'], self.admin.id)
        self.assertEqual(res.data['slug'], slugify(payload['title']))

    def test_update_post_success(self):
        """Test that updating a post is successful."""
        post = create_post(user=self.admin)
        payload = {
            'title': 'New title',
            'tags': [
                {'name': 'tag1'},
                {'name': 'tag2'}
            ]
        }
        url = detail_url(post.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], payload['title'])
        self.assertEqual(len(res.data['tags']), 2)
        self.assertEqual(res.data['tags'][0]['name'], payload['tags'][0]['name'])
        self.assertEqual(res.data['tags'][1]['name'], payload['tags'][1]['name'])

    def test_delete_post_success(self):
        """Test that deleting a post is successful."""
        post = create_post(user=self.admin)
        url = detail_url(post.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        post_exists = Post.objects.filter(id=post.id).exists()
        self.assertFalse(post_exists)