from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()
PASSWORD = "tether-alert-2026!"


class AdminAccessTests(TestCase):
    def test_non_staff_user_is_redirected_to_admin_login(self):
        user = User.objects.create_user("user@example.com", PASSWORD)
        self.client.force_login(user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)


class UserAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@example.com", PASSWORD)
        self.user = User.objects.create_user("user@example.com", PASSWORD)
        self.client.force_login(self.admin)
        self.changelist = reverse("admin:accounts_user_changelist")

    def test_changelist_searches_by_email(self):
        response = self.client.get(self.changelist, {"q": "user@"})
        self.assertContains(response, "user@example.com")
        self.assertNotContains(response, "admin@example.com</a>")

    def test_deactivate_and_reactivate_actions(self):
        self.client.post(self.changelist, {
            "action": "deactivate_users", "_selected_action": [self.user.pk],
        })
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.client.post(self.changelist, {
            "action": "reactivate_users", "_selected_action": [self.user.pk],
        })
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
