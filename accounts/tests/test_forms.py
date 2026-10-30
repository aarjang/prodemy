from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.forms import SignUpForm

User = get_user_model()
PASSWORD = "tether-alert-2026!"


class SignUpFormTests(TestCase):
    def form(self, email="Ali@Example.com", password1=PASSWORD, password2=PASSWORD):
        return SignUpForm(data={"email": email, "password1": password1, "password2": password2})

    def test_valid_signup_lowercases_email(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, "ali@example.com")
        self.assertTrue(user.check_password(PASSWORD))

    def test_existing_email_in_any_case_is_rejected(self):
        User.objects.create_user("ali@example.com", PASSWORD)
        form = self.form(email="ALI@example.COM")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("قبلاً", form.errors["email"][0])

    def test_password_mismatch_is_rejected(self):
        form = self.form(password2="something-else-99")
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_password_validators_apply(self):
        form = self.form(password1="123", password2="123")
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_invalid_email_is_rejected(self):
        self.assertFalse(self.form(email="not-an-email").is_valid())
