"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
PROFILE_URL = reverse('user:profile')

SAMPLE_USER_DETAILS = {
    'email': 'test@example.com',
    'password': 'password123',
    'first_name': 'John',
    'date_of_birth': '1980-12-12'
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
        res = self.client.post(CREATE_USER_URL, SAMPLE_USER_DETAILS)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=SAMPLE_USER_DETAILS['email'])
        self.assertTrue(user.check_password(SAMPLE_USER_DETAILS['password']))
        self.assertEqual(user.first_name, SAMPLE_USER_DETAILS['first_name'])
        self.assertEqual(user.date_of_birth.strftime('%Y-%m-%d'), SAMPLE_USER_DETAILS['date_of_birth'])

        # Check that the API is secure and does not send password in plain text in response
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        create_user(**SAMPLE_USER_DETAILS)
        res = self.client.post(CREATE_USER_URL, SAMPLE_USER_DETAILS)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_required_field_error(self):
        """Test that if the required field is not present, an error is raised."""
        payload_1 = {
            'email': 'email@example.com',
            'password': 'password123',
            'date_of_birth': '2000-01-01'
        }
        r1 = self.client.post(CREATE_USER_URL, payload_1)

        payload_2 = {
            'email': 'email@example.com',
            'password': 'password123',
            'first_name': 'Amy'
        }
        r2 = self.client.post(CREATE_USER_URL, payload_2)

        self.assertEqual(r1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            'email': 'u@example.com',
            'password': '123',
            'first_name': 'Carol',
            'date_of_birth': '2000-06-06'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        create_user(**SAMPLE_USER_DETAILS)

        payload = {
            'email': SAMPLE_USER_DETAILS['email'],
            'password': SAMPLE_USER_DETAILS['password'],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials are invalid."""

        create_user(**SAMPLE_USER_DETAILS)

        payload = {'email': SAMPLE_USER_DETAILS['email'], 'password': 'wrongPassword'}
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
            password='password123',
            first_name='Adam',
            date_of_birth='1970-07-07'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('email', res.data)
        self.assertIn('first_name', res.data)
        self.assertIn('last_name', res.data)
        self.assertIn('date_of_birth', res.data)
        self.assertIn('created_at', res.data)
        self.assertEqual(res.data['email'], self.user.email)
        self.assertEqual(res.data['first_name'], self.user.first_name)

    def test_post_profile_not_allowed(self):
        """Test POST is not allowed for the 'profile' endpoint."""
        res = self.client.post(PROFILE_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            'last_name': 'SomeName',
            'password': 'newPassword'
        }
        res = self.client.patch(PROFILE_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.last_name, payload['last_name'])
        self.assertTrue(self.user.check_password(payload['password']))
