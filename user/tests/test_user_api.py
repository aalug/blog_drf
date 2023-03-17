"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')


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
        payload = {
            'email': 'user@example.com',
            'password': 'password123',
            'first_name': 'Julia',
            'date_of_birth': '2000-10-10'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertEqual(user.first_name, payload['first_name'])
        self.assertEqual(user.date_of_birth.strftime('%Y-%m-%d'), payload['date_of_birth'])

        # Check that the API is secure and does not send password in plain text in response
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'Anna',
            'date_of_birth': '2000-02-02'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

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
