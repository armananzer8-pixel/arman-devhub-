
# ============================================
# ARMAN DEVHUB
# DAY 186 - FORMVIEW AND SUCCESS MESSAGES
# ============================================

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import ContactMessage, MessageNote


class MessageNoteFormViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff = User.objects.create_user(
            username="day186_staff",
            password="ExampleTestPass!186",
            is_staff=True
        )

        cls.regular_user = User.objects.create_user(
            username="day186_regular",
            password="ExampleTestPass!186"
        )

        cls.message = ContactMessage.objects.create(
            name="Day 186 Student",
            email="day186@example.com",
            message="Testing the Django FormView."
        )

    def note_url(self):

        return reverse(
            "message_add_note",
            kwargs={"pk": self.message.pk}
        )

    def detail_url(self):

        return reverse(
            "message_detail",
            kwargs={"pk": self.message.pk}
        )

    # ========================================
    # TEST 1 - STAFF CAN OPEN FORM
    # ========================================

    def test_staff_can_open_note_form(self):

        self.client.force_login(self.staff)

        response = self.client.get(self.note_url())

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/message_note_form.html"
        )

        self.assertContains(
            response,
            "Day 186 Student"
        )

        self.assertContains(
            response,
            "Save Note"
        )

    # ========================================
    # TEST 2 - VALID POST CREATES A NOTE
    # ========================================

    def test_valid_post_creates_note(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.note_url(),
            {
                "note": "Follow up with this student."
            }
        )

        self.assertRedirects(
            response,
            self.detail_url(),
            fetch_redirect_response=False
        )

        self.assertTrue(
            MessageNote.objects.filter(
                contact_message=self.message,
                note="Follow up with this student."
            ).exists()
        )

    # ========================================
    # TEST 3 - SUCCESS MESSAGE IS DISPLAYED
    # ========================================

    def test_success_message_after_redirect(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.note_url(),
            {
                "note": "Reviewed the contact message."
            },
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Note added successfully."
        )

        self.assertContains(
            response,
            "Reviewed the contact message."
        )

    # ========================================
    # TEST 4 - INVALID NOTE IS NOT SAVED
    # ========================================

    def test_invalid_note_is_not_saved(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.note_url(),
            {
                "note": "A"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Note must contain at least 3 characters."
        )

        self.assertEqual(
            MessageNote.objects.filter(
                contact_message=self.message
            ).count(),
            0
        )

    # ========================================
    # TEST 5 - GUEST ACCESS IS BLOCKED
    # ========================================

    def test_guest_cannot_add_note(self):

        for method in ["get", "post"]:

            with self.subTest(method=method):

                response = getattr(
                    self.client,
                    method
                )(
                    self.note_url(),
                    {"note": "Unauthorized note."}
                    if method == "post"
                    else {}
                )

                self.assertEqual(
                    response.status_code,
                    302
                )

        self.assertFalse(
            MessageNote.objects.filter(
                contact_message=self.message
            ).exists()
        )

    # ========================================
    # TEST 6 - NON-STAFF ACCESS IS BLOCKED
    # ========================================

    def test_regular_user_cannot_add_note(self):

        self.client.force_login(self.regular_user)

        for method in ["get", "post"]:

            with self.subTest(method=method):

                response = getattr(
                    self.client,
                    method
                )(
                    self.note_url(),
                    {"note": "Unauthorized note."}
                    if method == "post"
                    else {}
                )

                self.assertEqual(
                    response.status_code,
                    302
                )

        self.assertFalse(
            MessageNote.objects.filter(
                contact_message=self.message
            ).exists()
        )
