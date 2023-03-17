"""
Test fpr models.
"""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase


def create_user(user_details: dict[str, str]):
    """Create and return a new user."""
    payload = {
        'email': 'user@example.com',
        'password': 'password123',
        'first_name': 'First',
        'date_of_birth': '1950-10-10'
    }
    payload.update(user_details)
    return get_user_model().objects.create_user(payload)


class ModelTest(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'test123'
        first_name = 'John'
        date_of_birth = datetime.datetime(day=1, month=1, year=2011)
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            date_of_birth=date_of_birth
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='password123',
                first_name='Adam',
                date_of_birth='2012-12-12'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='password123',
                first_name='Marc',
                date_of_birth='2012-12-12'
            )

    def test_new_user_with_too_short_password_raise_error(self):
        """Test that creating a user without a password raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='testUser5@example.com',
                password='test1',
                first_name='Carl',
                date_of_birth='2012-12-12'
            )

    def test_new_user_with_6_chars_password_success(self):
        """Test that creating a user with a password 6 characters
           does not raise a ValueError."""
        get_user_model().objects.create_user(
            email='testUser6@example.com',
            password='test12',
            first_name='Joe',
            date_of_birth='2012-12-12'
        )
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='admin123',
            first_name='Admin',
            date_of_birth='1999-09-09'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
