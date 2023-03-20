"""
Tests for the user API.
"""
import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import UserProfile

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
PROFILE_URL = reverse('user:profile')

SAMPLE_USER_DETAILS = {
    'email': 'test@example.com',
    'username': 'some_user',
    'password': 'password123'
}


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public (that do not require authentication)
       features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        res = self.client.post(CREATE_USER_URL, {'user': {**SAMPLE_USER_DETAILS}}, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=SAMPLE_USER_DETAILS['email'])
        self.assertTrue(user.check_password(SAMPLE_USER_DETAILS['password']))

        # Check that the API is secure and does not send password in plain text in response
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        details = {
            'email': 'g@g.com',
            'username': 'user12',
            'password': '123123'
        }
        user = create_user(**details)
        res = self.client.post(CREATE_USER_URL, {'user': {**details}}, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            'user': {
                'email': 'u@example.com',
                'username': 'user',
                'password': '123'
            }
        }
        res = self.client.post(CREATE_USER_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['user']['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        details = {
            'email': 'x@x.com',
            'username': 'aaa2',
            'password': '123123'
        }
        create_user(**details)

        payload = {
            'email': details['email'],
            'password': details['password']
        }
        res = self.client.post(TOKEN_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials are invalid."""

        user = create_user(email='e@e.com', username='user23', password='password')

        payload = {'email': user.email, 'password': 'wrongPassword'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test returns error if the user with given email cannot be found."""
        payload = {'email': 'email@example.com', 'password': 'pass123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test6@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required to get to the users profile."""
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email='user@example.com',
            username='username',
            password='password123'
        )
        UserProfile.objects.create(
            user=self.user
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(PROFILE_URL)
        user = res.data['user']

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('user', res.data)
        self.assertEqual(user['email'], self.user.email)
        self.assertEqual(user['username'], self.user.username)
        self.assertIn('first_name', res.data)
        self.assertIn('last_name', res.data)
        self.assertIn('date_of_birth', res.data)
        self.assertIn('profile_image', res.data)

    def test_post_profile_not_allowed(self):
        """Test POST is not allowed for the 'profile' endpoint."""
        res = self.client.post(PROFILE_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_password(self):
        """Test updating the user password."""
        payload = {'user': {'password': 'newPassword'}}
        res = self.client.patch(PROFILE_URL, payload, format='json')

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(payload['user']['password']))

    def test_update_email_not_allowed(self):
        """Test that updating an email is not allowed."""
        payload = {'user': {'email': 'new_email@example.com'}}
        res = self.client.patch(PROFILE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_username_not_allowed(self):
        """Test that updating a username is not allowed."""
        payload = {'user': {'username': 'new_username'}}
        res = self.client.patch(PROFILE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile_success(self):
        """Test updating profile information is successful."""
        date_of_birth = datetime.date(year=1950, month=5, day=5)
        payload = {
            'first_name': 'John',
            'last_name': 'Something',
            'date_of_birth': date_of_birth.strftime('%Y-%m-%d')
        }
        res = self.client.patch(PROFILE_URL, payload, format='json')
        profile = UserProfile.objects.filter(user=self.user).first()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.first_name, payload['first_name'])
        self.assertEqual(profile.last_name, payload['last_name'])
        self.assertEqual(profile.date_of_birth, date_of_birth)
