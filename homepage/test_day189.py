
# ============================================
# ARMAN DEVHUB
# DAY 189 - ATTACHMENT DELETE TESTS
# ============================================

from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import ContactMessage, MessageAttachment


class MessageAttachmentDeleteTests(TestCase):

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
            username="day189_staff",
            password="ExamplePass!189",
            is_staff=True
        )

        self.regular_user = User.objects.create_user(
            username="day189_regular",
            password="ExamplePass!189"
        )

        self.message = ContactMessage.objects.create(
            name="Day 189 Student",
            email="day189@example.com",
            message="Testing attachment deletion."
        )

    # ---------------------------------
    # HELPER METHODS
    # ---------------------------------

    def create_attachment(self, name="day189_notes.txt"):

        return MessageAttachment.objects.create(
            contact_message=self.message,
            file=SimpleUploadedFile(
                name,
                b"Day 189 sample attachment.",
                content_type="text/plain"
            )
        )

    def delete_url(self, attachment):

        return reverse(
            "message_attachment_delete",
            kwargs={"pk": attachment.pk}
        )

    # =================================
    # TEST 1 - STAFF OPENS CONFIRMATION
    # =================================

    def test_staff_can_open_confirmation(self):

        attachment = self.create_attachment()

        self.client.force_login(self.staff)

        response = self.client.get(
            self.delete_url(attachment)
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/message_attachment_confirm_delete.html"
        )

        self.assertContains(
            response,
            "Yes, Delete Attachment"
        )

    # =================================
    # TEST 2 - GET NEVER DELETES
    # =================================

    def test_get_does_not_delete_attachment(self):

        attachment = self.create_attachment()

        self.client.force_login(self.staff)

        self.client.get(
            self.delete_url(attachment)
        )

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=attachment.pk
            ).exists()
        )

        self.assertTrue(
            attachment.file.storage.exists(
                attachment.file.name
            )
        )

    # =================================
    # TEST 3 - POST DELETES DATABASE ROW
    # =================================

    def test_post_deletes_attachment_record(self):

        attachment = self.create_attachment()

        self.client.force_login(self.staff)

        response = self.client.post(
            self.delete_url(attachment),
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            MessageAttachment.objects.filter(
                pk=attachment.pk
            ).exists()
        )

        self.assertContains(
            response,
            "Attachment deleted successfully."
        )

    # =================================
    # TEST 4 - STORED FILE IS REMOVED
    # =================================

    def test_stored_file_removed_after_commit(self):

        attachment = self.create_attachment()

        storage = attachment.file.storage
        file_name = attachment.file.name

        self.assertTrue(
            storage.exists(file_name)
        )

        self.client.force_login(self.staff)

        # Django TestCase rolls back its
        # transaction. Execute the captured
        # on_commit callbacks explicitly.
        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            self.client.post(
                self.delete_url(attachment)
            )

        self.assertEqual(len(callbacks), 1)

        self.assertFalse(
            storage.exists(file_name)
        )

    # =================================
    # TEST 5 - OTHER FILE IS PRESERVED
    # =================================

    def test_other_attachment_is_not_deleted(self):

        first = self.create_attachment("first.txt")
        second = self.create_attachment("second.txt")

        second_name = second.file.name
        second_storage = second.file.storage

        self.client.force_login(self.staff)

        with self.captureOnCommitCallbacks(execute=True):

            self.client.post(
                self.delete_url(first)
            )

        self.assertFalse(
            MessageAttachment.objects.filter(
                pk=first.pk
            ).exists()
        )

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=second.pk
            ).exists()
        )

        self.assertTrue(
            second_storage.exists(second_name)
        )

    # =================================
    # TEST 6 - GUEST IS BLOCKED
    # =================================

    def test_guest_cannot_delete(self):

        attachment = self.create_attachment()

        url = self.delete_url(attachment)

        self.assertEqual(
            self.client.get(url).status_code,
            302
        )

        self.assertEqual(
            self.client.post(url).status_code,
            302
        )

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=attachment.pk
            ).exists()
        )

    # =================================
    # TEST 7 - NON-STAFF IS BLOCKED
    # =================================

    def test_regular_user_cannot_delete(self):

        attachment = self.create_attachment()

        self.client.force_login(self.regular_user)

        url = self.delete_url(attachment)

        self.assertEqual(
            self.client.get(url).status_code,
            302
        )

        self.assertEqual(
            self.client.post(url).status_code,
            302
        )

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=attachment.pk
            ).exists()
        )

    # =================================
    # TEST 8 - MISSING ATTACHMENT
    # =================================

    def test_missing_attachment_returns_404(self):

        self.client.force_login(self.staff)

        url = reverse(
            "message_attachment_delete",
            kwargs={"pk": 9999999}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            404
        )

    # =================================
    # TEST 9 - HTTP DELETE IS DISALLOWED
    # =================================

    def test_http_delete_method_is_blocked(self):

        attachment = self.create_attachment()

        self.client.force_login(self.staff)

        response = self.client.delete(
            self.delete_url(attachment)
        )

        self.assertEqual(
            response.status_code,
            405
        )

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=attachment.pk
            ).exists()
        )
