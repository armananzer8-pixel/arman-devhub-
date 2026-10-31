
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .forms import StaffContactMessageForm
from .models import ContactMessage


class StaffFormValidationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.staff = User.objects.create_user(
            username="day185_staff",
            password="ExamplePass!185",
            is_staff=True
        )

        cls.message = ContactMessage.objects.create(
            name="Original Sender",
            email="original@example.com",
            message="Original database message"
        )

    def valid_data(self):
        return {
            "name": "Test Student",
            "email": "student@example.com",
            "message": "I am learning Django validation."
        }

    # TEST 1
    def test_valid_form_trims_whitespace(self):
        data = self.valid_data()
        data["name"] = "  Test Student  "

        form = StaffContactMessageForm(data=data)

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["name"],
            "Test Student"
        )

    # TEST 2
    def test_short_name_rejected(self):
        data = self.valid_data()
        data["name"] = "A"

        form = StaffContactMessageForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Name must contain at least 2 characters.",
            form.errors["name"]
        )

    # TEST 3
    def test_short_message_rejected(self):
        data = self.valid_data()
        data["message"] = "Hello"

        form = StaffContactMessageForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Message must be at least 10 characters long.",
            form.errors["message"]
        )

    # TEST 4
    def test_invalid_email_rejected(self):
        data = self.valid_data()
        data["email"] = "wrong-email"

        form = StaffContactMessageForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Please enter a valid email address.",
            form.errors["email"]
        )

    # TEST 5
    def test_identical_name_and_message_rejected(self):
        data = self.valid_data()
        data["name"] = "Same Content"
        data["message"] = "Same Content"

        form = StaffContactMessageForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn(
            "Message cannot be identical to the sender's name.",
            form.non_field_errors()
        )

    # TEST 6
    def test_invalid_update_keeps_old_data(self):
        self.client.force_login(self.staff)

        url = reverse(
            "message_edit",
            kwargs={"pk": self.message.pk}
        )

        response = self.client.post(
            url,
            {
                "name": "Changed Name",
                "email": "changed@example.com",
                "message": "Short"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.name,
            "Original Sender"
        )
        self.assertEqual(
            self.message.email,
            "original@example.com"
        )

        self.assertContains(
            response,
            "Message must be at least 10 characters long."
        )

    # TEST 7
    def test_valid_create_saves_cleaned_data(self):
        self.client.force_login(self.staff)

        data = self.valid_data()
        data["name"] = "  Test Student  "

        response = self.client.post(
            reverse("message_create"),
            data
        )

        created = ContactMessage.objects.get(
            email="student@example.com"
        )

        self.assertEqual(created.name, "Test Student")

        self.assertRedirects(
            response,
            reverse(
                "message_detail",
                kwargs={"pk": created.pk}
            ),
            fetch_redirect_response=False
        )
