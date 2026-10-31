
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, MessageAttachment


User = get_user_model()


class AttachmentAnalyticsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.temp_media = TemporaryDirectory()
        cls.media_override = override_settings(
            MEDIA_ROOT=cls.temp_media.name
        )
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.temp_media.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="day194_staff",
            password="TestPass194!",
            is_staff=True,
        )

        self.message = ContactMessage.objects.create(
            name="Day 194 Student",
            email="day194@example.com",
            message="Testing attachment analytics.",
        )

        self.url = reverse("attachment_dashboard")

    def create_attachment(self, filename):
        return MessageAttachment.objects.create(
            contact_message=self.message,
            file=SimpleUploadedFile(
                filename,
                b"Sample attachment content",
            ),
        )

    def test_empty_dashboard_statistics(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["analytics"]["total_attachments"],
            0,
        )
        self.assertEqual(
            response.context["analytics"][
                "messages_with_attachments"
            ],
            0,
        )

    def test_total_attachment_count(self):
        self.create_attachment("first.pdf")
        self.create_attachment("second.txt")

        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)

        self.assertEqual(
            response.context["analytics"]["total_attachments"],
            2,
        )

    def test_distinct_message_count(self):
        self.create_attachment("first.pdf")
        self.create_attachment("second.txt")

        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)

        self.assertEqual(
            response.context["analytics"][
                "messages_with_attachments"
            ],
            1,
        )

    def test_file_type_statistics(self):
        self.create_attachment("guide.pdf")
        self.create_attachment("notes.txt")
        self.create_attachment("another.pdf")

        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)

        counts = response.context["analytics"][
            "file_type_counts"
        ]

        self.assertEqual(counts[".pdf"], 2)
        self.assertEqual(counts[".txt"], 1)
        self.assertEqual(counts[".jpg"], 0)

    def test_chart_data_uses_all_attachment_types(self):
        for filename in (
            "guide.pdf",
            "notes.txt",
            "photo.jpg",
            "diagram.png",
            "animation.gif",
            "report.doc",
            "report.docx",
            "archive.zip",
        ):
            self.create_attachment(filename)

        self.client.force_login(self.staff_user)
        response = self.client.get(
            self.url,
            {"q": "guide"},
        )

        self.assertEqual(
            response.context["attachment_chart_data"],
            {
                "labels": [
                    "PDF",
                    "TXT",
                    "Images",
                    "GIF",
                    "Word Documents",
                    "Other",
                ],
                "counts": [1, 1, 2, 1, 2, 1],
            },
        )

    def test_analytics_not_affected_by_search(self):
        self.create_attachment("python.pdf")
        self.create_attachment("django.txt")

        self.client.force_login(self.staff_user)

        response = self.client.get(
            self.url,
            {"q": "python"},
        )

        self.assertEqual(
            response.context["analytics"]["total_attachments"],
            2,
        )
        self.assertEqual(
            response.context["total_attachments"],
            1,
        )

    def test_dashboard_displays_analytics(self):
        self.create_attachment("report.pdf")

        self.client.force_login(self.staff_user)
        response = self.client.get(self.url)

        self.assertContains(
            response,
            "Attachment Analytics",
        )
        self.assertContains(
            response,
            "Messages With Attachments",
        )

    def test_regular_user_cannot_access_analytics(self):
        regular_user = User.objects.create_user(
            username="day194_regular",
            password="TestPass194!",
        )

        self.client.force_login(regular_user)
        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)
