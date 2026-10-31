
# ==========================================
# DAY 192 - ATTACHMENT DASHBOARD TESTS
# ==========================================

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, MessageAttachment


class AttachmentDashboardTests(TestCase):

    def setUp(self):

        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)

        media_settings = override_settings(
            MEDIA_ROOT=self.temp_media.name
        )
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        User = get_user_model()

        self.staff = User.objects.create_user(
            username="day192_staff",
            password="ExamplePass!192",
            is_staff=True
        )

        self.regular_user = User.objects.create_user(
            username="day192_regular",
            password="ExamplePass!192"
        )

        self.message = ContactMessage.objects.create(
            name="Day 192 Student",
            email="day192@example.com",
            message="Dashboard testing."
        )

        self.attachment = MessageAttachment.objects.create(
            contact_message=self.message,
            file=SimpleUploadedFile(
                "python_notes_192.txt",
                b"Learning Django file metadata.",
                content_type="text/plain"
            )
        )

        self.url = reverse(
            "attachment_dashboard"
        )

    def test_staff_can_open_dashboard(self):

        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 200
        )

        self.assertTemplateUsed(
            response,
            "homepage/attachment_dashboard.html"
        )

    def test_guest_is_redirected(self):

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 302
        )

    def test_regular_user_is_blocked(self):

        self.client.force_login(
            self.regular_user
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code, 302
        )

    def test_filename_is_displayed(self):

        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "python_notes_192.txt"
        )

    def test_file_extension_is_displayed(self):

        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertContains(
            response,
            ".txt"
        )

    def test_search_finds_attachment(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"q": "python_notes"}
        )

        self.assertContains(
            response,
            "python_notes_192.txt"
        )

        self.assertEqual(
            response.context[
                "total_attachments"
            ],
            1
        )

    def test_search_excludes_unmatched_attachment(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"q": "does_not_exist"}
        )

        self.assertEqual(
            response.context[
                "total_attachments"
            ],
            0
        )

        self.assertContains(
            response,
            "No attachments found."
        )

    def test_dashboard_has_attachment_actions(self):

        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        replace_url = reverse(
            "message_attachment_replace",
            kwargs={"pk": self.attachment.pk}
        )

        delete_url = reverse(
            "message_attachment_delete",
            kwargs={"pk": self.attachment.pk}
        )

        self.assertContains(
            response,
            replace_url
        )

        self.assertContains(
            response,
            delete_url
        )
