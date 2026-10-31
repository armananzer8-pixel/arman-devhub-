
# =====================================
# ARMAN DEVHUB
# DAY 187 - REUSABLE MIXIN TESTS
# =====================================

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import ContactMessage


class ReusableMixinTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff = User.objects.create_user(
            username="day187_staff",
            password="ExamplePass!187",
            is_staff=True
        )

        cls.regular_user = User.objects.create_user(
            username="day187_regular",
            password="ExamplePass!187"
        )

        cls.message = ContactMessage.objects.create(
            name="Original Student",
            email="original187@example.com",
            message="Original message for Day 187."
        )

    def valid_data(self):

        return {
            "name": "Test Student",
            "email": "test187@example.com",
            "message": "Learning reusable Django mixins."
        }

    def edit_url(self):

        return reverse(
            "message_edit",
            kwargs={"pk": self.message.pk}
        )

    # ==================================
    # TEST 1 - CREATE SUCCESS MESSAGE
    # ==================================

    def test_create_success_message(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("message_create"),
            self.valid_data(),
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Contact message for Test Student created successfully."
        )

        self.assertTrue(
            ContactMessage.objects.filter(
                email="test187@example.com"
            ).exists()
        )

    # ==================================
    # TEST 2 - UPDATE SUCCESS MESSAGE
    # ==================================

    def test_update_success_message(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.edit_url(),
            {
                "name": "Updated Student",
                "email": "updated187@example.com",
                "message": "Updated successfully on Day 187."
            },
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Contact message for Updated Student updated successfully."
        )

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.name,
            "Updated Student"
        )

    # ==================================
    # TEST 3 - INVALID CREATE
    # ==================================

    def test_invalid_create_does_not_save(self):

        self.client.force_login(self.staff)

        count_before = ContactMessage.objects.count()

        response = self.client.post(
            reverse("message_create"),
            {
                "name": "A",
                "email": "invalid-email",
                "message": "Short"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            ContactMessage.objects.count(),
            count_before
        )

        self.assertNotContains(
            response,
            "created successfully."
        )

    # ==================================
    # TEST 4 - INVALID UPDATE
    # ==================================

    def test_invalid_update_keeps_original(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.edit_url(),
            {
                "name": "Modified",
                "email": "modified@example.com",
                "message": "Short"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.name,
            "Original Student"
        )

        self.assertNotContains(
            response,
            "updated successfully."
        )

    # ==================================
    # TEST 5 - GUEST ACCESS
    # ==================================

    def test_guest_is_redirected(self):

        urls = [
            reverse("message_create"),
            self.edit_url()
        ]

        for url in urls:

            with self.subTest(url=url):

                get_response = self.client.get(url)

                post_response = self.client.post(
                    url,
                    self.valid_data()
                )

                self.assertEqual(
                    get_response.status_code,
                    302
                )

                self.assertEqual(
                    post_response.status_code,
                    302
                )

    # ==================================
    # TEST 6 - NON-STAFF ACCESS
    # ==================================

    def test_regular_user_is_redirected(self):

        self.client.force_login(self.regular_user)

        urls = [
            reverse("message_create"),
            self.edit_url()
        ]

        for url in urls:

            with self.subTest(url=url):

                get_response = self.client.get(url)

                post_response = self.client.post(
                    url,
                    self.valid_data()
                )

                self.assertEqual(
                    get_response.status_code,
                    302
                )

                self.assertEqual(
                    post_response.status_code,
                    302
                )
