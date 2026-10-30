import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
PASSWORD = "tether-alert-2026!"


class SignUpViewTests(TestCase):
    url = reverse("accounts:signup")

    def test_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ثبت‌نام")
        self.assertContains(response, 'for="id_email"')

    def test_signup_creates_user_signs_in_and_redirects(self):
        response = self.client.post(
            self.url, {"email": "new@example.com", "password1": PASSWORD, "password2": PASSWORD}
        )
        self.assertRedirects(response, reverse("alerts:list"), fetch_redirect_response=False)
        user = User.objects.get(email="new@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_email_shows_error(self):
        User.objects.create_user("new@example.com", PASSWORD)
        response = self.client.post(
            self.url, {"email": "NEW@example.com", "password1": PASSWORD, "password2": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "قبلاً")
        self.assertEqual(User.objects.count(), 1)

    def test_signed_in_user_is_redirected_away(self):
        user = User.objects.create_user("a@example.com", PASSWORD)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("alerts:list"), fetch_redirect_response=False)


class LoginLogoutTests(TestCase):
    login_url = reverse("login")

    def setUp(self):
        self.user = User.objects.create_user("ali@example.com", PASSWORD)

    def test_login_page_uses_email_label(self):
        response = self.client.get(self.login_url)
        self.assertContains(response, "ایمیل")
        self.assertContains(response, reverse("accounts:signup"))
        self.assertContains(response, reverse("password_reset"))

    def test_login_with_email_in_any_case(self):
        response = self.client.post(self.login_url, {"username": "ALI@example.com", "password": PASSWORD})
        self.assertRedirects(response, reverse("alerts:list"), fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_shows_one_generic_error(self):
        response = self.client.post(self.login_url, {"username": "ali@example.com", "password": "wrong-pass"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        form = response.context["form"]
        self.assertEqual(len(form.non_field_errors()), 1)
        self.assertFalse(form.errors.get("username"))
        self.assertFalse(form.errors.get("password"))

    def test_unknown_email_shows_the_same_error(self):
        wrong_pass = self.client.post(self.login_url, {"username": "ali@example.com", "password": "nope-123"})
        unknown = self.client.post(self.login_url, {"username": "who@example.com", "password": "nope-123"})
        self.assertEqual(
            wrong_pass.context["form"].non_field_errors(), unknown.context["form"].non_field_errors()
        )

    def test_inactive_user_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save()
        self.client.post(self.login_url, {"username": "ali@example.com", "password": PASSWORD})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_is_post_and_redirects_home(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("core:home"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)


class PasswordResetTests(TestCase):
    url = reverse("password_reset")

    def setUp(self):
        User.objects.create_user("ali@example.com", PASSWORD)

    def test_reset_email_link_sets_new_password(self):
        response = self.client.post(self.url, {"email": "ali@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ali@example.com"])
        link = re.search(r"https?://[^/\s]+(/accounts/reset/\S+/)", mail.outbox[0].body).group(1)

        form_page = self.client.get(link, follow=True)
        self.assertEqual(form_page.status_code, 200)
        new_password = "brand-new-pass-2026!"
        done = self.client.post(
            form_page.redirect_chain[-1][0],
            {"new_password1": new_password, "new_password2": new_password},
        )
        self.assertRedirects(done, reverse("password_reset_complete"))
        self.assertTrue(User.objects.get(email="ali@example.com").check_password(new_password))

    def test_unknown_email_shows_same_sent_page(self):
        response = self.client.post(self.url, {"email": "nobody@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_pages_render_in_persian(self):
        self.assertContains(self.client.get(self.url), "بازیابی رمز عبور")
        self.assertContains(self.client.get(reverse("password_reset_done")), "ایمیل")
