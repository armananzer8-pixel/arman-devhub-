
# ============================================
# ARMAN DEVHUB
# DAY 188 - FILE UPLOAD TESTS
# ============================================

from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import ContactMessage, MessageAttachment


class MessageAttachmentTests(TestCase):

    def setUp(self):

        # Keep test files separate from real uploads
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)

        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media.name
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        User = get_user_model()

        self.staff = User.objects.create_user(
            username="day188_staff",
            password="ExamplePass!188",
            is_staff=True
        )

        self.regular_user = User.objects.create_user(
            username="day188_regular",
            password="ExamplePass!188"
        )

        self.message = ContactMessage.objects.create(
            name="Day 188 Student",
            email="day188@example.com",
            message="Testing secure Django file uploads."
        )

    # =====================================
    # HELPER METHODS
    # =====================================

    def upload_url(self):
        return reverse(
            "message_attachment_upload",
            kwargs={"pk": self.message.pk}
        )

    def sample_file(self):
        return SimpleUploadedFile(
            "day188_notes.txt",
            b"Day 188 file upload test.",
            content_type="text/plain"
        )

    def create_attachment(self):
        return MessageAttachment.objects.create(
            contact_message=self.message,
            file=self.sample_file()
        )

    # =====================================
    # TEST 1 - STAFF CAN OPEN UPLOAD FORM
    # =====================================

    def test_staff_can_open_upload_form(self):

        self.client.force_login(self.staff)

        response = self.client.get(self.upload_url())

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/message_attachment_form.html"
        )

        self.assertContains(
            response,
            "Upload Attachment"
        )

    # =====================================
    # TEST 2 - STAFF CAN UPLOAD A FILE
    # =====================================

    def test_staff_can_upload_file(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.upload_url(),
            {"file": self.sample_file()},
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            MessageAttachment.objects.count(),
            1
        )

        attachment = MessageAttachment.objects.get()

        self.assertEqual(
            attachment.contact_message,
            self.message
        )

        self.assertTrue(
            attachment.file.storage.exists(
                attachment.file.name
            )
        )

        self.assertContains(
            response,
            "Attachment uploaded successfully."
        )

    # =====================================
    # TEST 3 - INVALID FILE TYPE
    # =====================================

    def test_unsupported_extension_rejected(self):

        self.client.force_login(self.staff)

        bad_file = SimpleUploadedFile(
            "example.exe",
            b"This is test data only.",
            content_type="application/octet-stream"
        )

        response = self.client.post(
            self.upload_url(),
            {"file": bad_file}
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Only PDF and TXT files are allowed."
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            0
        )

    # =====================================
    # TEST 4 - FILE SIZE VALIDATION
    # =====================================

    def test_large_file_rejected(self):

        self.client.force_login(self.staff)

        large_file = SimpleUploadedFile(
            "large.txt",
            b"x" * (1024 * 1024 + 1),
            content_type="text/plain"
        )

        response = self.client.post(
            self.upload_url(),
            {"file": large_file}
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "File size must not exceed 1 MB."
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            0
        )

    # =====================================
    # TEST 5 - INVALID PDF FILE
    # =====================================

    def test_invalid_pdf_rejected(self):

        self.client.force_login(self.staff)

        fake_pdf = SimpleUploadedFile(
            "invalid.pdf",
            b"This is not a PDF.",
            content_type="application/pdf"
        )

        response = self.client.post(
            self.upload_url(),
            {"file": fake_pdf}
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "The selected file is not a valid PDF."
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            0
        )

    # =====================================
    # TEST 6 - STAFF CAN DOWNLOAD
    # =====================================

    def test_staff_can_download_attachment(self):

        attachment = self.create_attachment()

        self.client.force_login(self.staff)

        url = reverse(
            "message_attachment_download",
            kwargs={"attachment_id": attachment.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "attachment",
            response["Content-Disposition"]
        )

        downloaded = b"".join(
            response.streaming_content
        )

        self.assertEqual(
            downloaded,
            b"Day 188 file upload test."
        )

        response.close()

    # =====================================
    # TEST 7 - GUEST ACCESS BLOCKED
    # =====================================

    def test_guest_cannot_upload_or_download(self):

        attachment = self.create_attachment()

        download_url = reverse(
            "message_attachment_download",
            kwargs={"attachment_id": attachment.pk}
        )

        self.assertEqual(
            self.client.get(
                self.upload_url()
            ).status_code,
            302
        )

        self.assertEqual(
            self.client.post(
                self.upload_url(),
                {"file": self.sample_file()}
            ).status_code,
            302
        )

        self.assertEqual(
            self.client.get(
                download_url
            ).status_code,
            302
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            1
        )

    # =====================================
    # TEST 8 - NON-STAFF ACCESS BLOCKED
    # =====================================

    def test_regular_user_cannot_upload_or_download(self):

        attachment = self.create_attachment()

        self.client.force_login(self.regular_user)

        download_url = reverse(
            "message_attachment_download",
            kwargs={"attachment_id": attachment.pk}
        )

        self.assertEqual(
            self.client.get(
                self.upload_url()
            ).status_code,
            302
        )

        self.assertEqual(
            self.client.post(
                self.upload_url(),
                {"file": self.sample_file()}
            ).status_code,
            302
        )

        self.assertEqual(
            self.client.get(
                download_url
            ).status_code,
            302
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            1
        )
