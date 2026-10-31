
# ============================================
# ARMAN DEVHUB
# DAY 191 - FILE REPLACEMENT TESTS
# ============================================

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, MessageAttachment


class MessageAttachmentReplaceTests(TestCase):

    def setUp(self):

        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)

        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media.name
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        User = get_user_model()

        self.staff = User.objects.create_user(
            username="day191_staff",
            password="ExamplePass!191",
            is_staff=True
        )

        self.regular_user = User.objects.create_user(
            username="day191_regular",
            password="ExamplePass!191"
        )

        self.message = ContactMessage.objects.create(
            name="Day 191 Student",
            email="day191@example.com",
            message="Testing attachment replacement."
        )

        self.attachment = MessageAttachment.objects.create(
            contact_message=self.message,
            file=SimpleUploadedFile(
                "original191.txt",
                b"Original file contents.",
                content_type="text/plain"
            )
        )

    def replace_url(self):

        return reverse(
            "message_attachment_replace",
            kwargs={"pk": self.attachment.pk}
        )

    def replacement_file(self):

        return SimpleUploadedFile(
            "updated191.txt",
            b"Updated file contents.",
            content_type="text/plain"
        )

    # =====================================
    # TEST 1 - STAFF OPENS FORM
    # =====================================

    def test_staff_can_open_replace_form(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            self.replace_url()
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "homepage/message_attachment_replace.html"
        )

        self.assertContains(
            response,
            "Replace Attachment"
        )

    # =====================================
    # TEST 2 - SUCCESSFUL REPLACEMENT
    # =====================================

    def test_staff_can_replace_attachment(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.replace_url(),
            {"file": self.replacement_file()},
            follow=True
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            1
        )

        self.attachment.refresh_from_db()

        self.assertIn(
            "updated191",
            self.attachment.file.name
        )

        self.assertContains(
            response,
            "Attachment replaced successfully."
        )

    # =====================================
    # TEST 3 - OLD FILE REMOVED
    # =====================================

    def test_old_file_removed_after_commit(self):

        old_name = self.attachment.file.name
        storage = self.attachment.file.storage

        self.assertTrue(storage.exists(old_name))

        self.client.force_login(self.staff)

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            self.client.post(
                self.replace_url(),
                {"file": self.replacement_file()}
            )

        self.assertEqual(len(callbacks), 1)

        self.assertFalse(storage.exists(old_name))

        self.attachment.refresh_from_db()

        self.assertTrue(
            storage.exists(
                self.attachment.file.name
            )
        )

    # =====================================
    # TEST 4 - INVALID EXTENSION
    # =====================================

    def test_invalid_extension_is_rejected(self):

        self.client.force_login(self.staff)

        old_name = self.attachment.file.name

        bad_file = SimpleUploadedFile(
            "invalid.exe",
            b"Not an allowed file.",
            content_type="application/octet-stream"
        )

        response = self.client.post(
            self.replace_url(),
            {"file": bad_file}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Only PDF and TXT files are allowed."
        )

        self.attachment.refresh_from_db()

        self.assertEqual(
            self.attachment.file.name,
            old_name
        )

    # =====================================
    # TEST 5 - LARGE FILE REJECTED
    # =====================================

    def test_large_file_is_rejected(self):

        self.client.force_login(self.staff)

        old_name = self.attachment.file.name

        large_file = SimpleUploadedFile(
            "large191.txt",
            b"x" * (1024 * 1024 + 1),
            content_type="text/plain"
        )

        response = self.client.post(
            self.replace_url(),
            {"file": large_file}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "File size must not exceed 1 MB."
        )

        self.attachment.refresh_from_db()

        self.assertEqual(
            self.attachment.file.name,
            old_name
        )

    # =====================================
    # TEST 6 - GUEST ACCESS BLOCKED
    # =====================================

    def test_guest_cannot_replace_attachment(self):

        self.assertEqual(
            self.client.get(
                self.replace_url()
            ).status_code,
            302
        )

        self.assertEqual(
            self.client.post(
                self.replace_url(),
                {"file": self.replacement_file()}
            ).status_code,
            302
        )

    # =====================================
    # TEST 7 - REGULAR USER BLOCKED
    # =====================================

    def test_regular_user_cannot_replace_attachment(self):

        self.client.force_login(self.regular_user)

        self.assertEqual(
            self.client.get(
                self.replace_url()
            ).status_code,
            302
        )

        self.assertEqual(
            self.client.post(
                self.replace_url(),
                {"file": self.replacement_file()}
            ).status_code,
            302
        )

    # =====================================
    # TEST 8 - MISSING ATTACHMENT
    # =====================================

    def test_missing_attachment_returns_404(self):

        self.client.force_login(self.staff)

        url = reverse(
            "message_attachment_replace",
            kwargs={"pk": 9999999}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            404
        )
