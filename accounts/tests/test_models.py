from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_email_is_stored_lowercased(self):
        user = User.objects.create_user("Ali@Example.COM", "a-strong-pass-123")
        self.assertEqual(user.email, "ali@example.com")

    def test_duplicate_email_in_different_case_is_rejected(self):
        User.objects.create_user("ali@example.com", "a-strong-pass-123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user("ALI@example.com", "another-pass-456")

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser("admin@example.com", "a-strong-pass-123")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_without_email_is_rejected(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", "a-strong-pass-123")

    def test_has_no_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertIsNone(User.username)

    def test_lookup_by_email_ignores_case(self):
        User.objects.create_user("ali@example.com", "a-strong-pass-123")
        self.assertEqual(User.objects.get_by_natural_key("ALI@EXAMPLE.com").email, "ali@example.com")
