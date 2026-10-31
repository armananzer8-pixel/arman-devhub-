
# ============================================
# ARMAN DEVHUB
# DAY 190 - SIGNAL FILE CLEANUP TESTS
# ============================================

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, MessageAttachment


class AutomaticFileCleanupTests(TestCase):

    def setUp(self):

        # Use temporary storage for tests.
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)

        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media.name
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        User = get_user_model()

        self.staff = User.objects.create_user(
            username="day190_staff",
            password="ExamplePass!190",
            is_staff=True
        )

        self.message = ContactMessage.objects.create(
            name="Day 190 Student",
            email="day190@example.com",
            message="Testing automatic Django file cleanup."
        )

    # =====================================
    # HELPER - CREATE TEST ATTACHMENTS
    # =====================================

    def create_attachment(self, filename="test190.txt"):

        return MessageAttachment.objects.create(
            contact_message=self.message,
            file=SimpleUploadedFile(
                filename,
                b"Day 190 signal cleanup test.",
                content_type="text/plain"
            )
        )

    # =====================================
    # TEST 1 - DIRECT DELETE CLEANS FILE
    # =====================================

    def test_direct_delete_removes_file(self):

        attachment = self.create_attachment()

        storage = attachment.file.storage
        filename = attachment.file.name
        attachment_id = attachment.pk

        self.assertTrue(storage.exists(filename))

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            attachment.delete()

        self.assertEqual(len(callbacks), 1)

        self.assertFalse(
            MessageAttachment.objects.filter(
                pk=attachment_id
            ).exists()
        )

        self.assertFalse(storage.exists(filename))

    # =====================================
    # TEST 2 - PARENT DELETE CLEANS FILES
    # =====================================

    def test_parent_delete_cleans_attachments(self):

        first = self.create_attachment("first190.txt")
        second = self.create_attachment("second190.txt")

        first_name = first.file.name
        second_name = second.file.name

        first_storage = first.file.storage
        second_storage = second.file.storage

        message_id = self.message.pk

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            self.message.delete()

        self.assertEqual(len(callbacks), 2)

        self.assertFalse(
            ContactMessage.objects.filter(
                pk=message_id
            ).exists()
        )

        self.assertEqual(
            MessageAttachment.objects.count(),
            0
        )

        self.assertFalse(
            first_storage.exists(first_name)
        )

        self.assertFalse(
            second_storage.exists(second_name)
        )

    # =====================================
    # TEST 3 - QUERYSET DELETE CLEANS FILES
    # =====================================

    def test_queryset_delete_cleans_files(self):

        first = self.create_attachment("bulk_first.txt")
        second = self.create_attachment("bulk_second.txt")

        first_storage = first.file.storage
        second_storage = second.file.storage

        first_name = first.file.name
        second_name = second.file.name

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            MessageAttachment.objects.filter(
                contact_message=self.message
            ).delete()

        self.assertEqual(len(callbacks), 2)

        self.assertEqual(
            MessageAttachment.objects.count(),
            0
        )

        self.assertFalse(
            first_storage.exists(first_name)
        )

        self.assertFalse(
            second_storage.exists(second_name)
        )

    # =====================================
    # TEST 4 - ROLLBACK KEEPS FILE
    # =====================================

    def test_rollback_preserves_file(self):

        attachment = self.create_attachment(
            "rollback190.txt"
        )

        attachment_id = attachment.pk

        storage = attachment.file.storage
        filename = attachment.file.name

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            try:
                with transaction.atomic():

                    attachment.delete()

                    # Simulate a database failure.
                    raise ValueError(
                        "Simulated transaction rollback"
                    )

            except ValueError:
                pass

        self.assertEqual(len(callbacks), 0)

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=attachment_id
            ).exists()
        )

        self.assertTrue(storage.exists(filename))

    # =====================================
    # TEST 5 - CLEANUP WAITS FOR COMMIT
    # =====================================

    def test_file_not_removed_before_commit(self):

        attachment = self.create_attachment(
            "pending190.txt"
        )

        storage = attachment.file.storage
        filename = attachment.file.name

        with self.captureOnCommitCallbacks() as callbacks:

            attachment.delete()

            # The file must still exist here.
            self.assertTrue(
                storage.exists(filename)
            )

        self.assertEqual(len(callbacks), 1)

        # We intentionally did not execute
        # the callbacks in this test.
        self.assertTrue(storage.exists(filename))

    # =====================================
    # TEST 6 - SHARED FILE IS PRESERVED
    # =====================================

    def test_shared_file_is_not_deleted_early(self):

        first = self.create_attachment(
            "shared190.txt"
        )

        filename = first.file.name
        storage = first.file.storage

        # Two database rows reference
        # the same stored file.
        second = MessageAttachment.objects.create(
            contact_message=self.message,
            file=filename
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            first.delete()

        self.assertTrue(storage.exists(filename))

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=second.pk
            ).exists()
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            second.delete()

        self.assertFalse(storage.exists(filename))

    # =====================================
    # TEST 7 - OTHER FILE IS PRESERVED
    # =====================================

    def test_unrelated_file_is_preserved(self):

        first = self.create_attachment(
            "delete_this190.txt"
        )

        second = self.create_attachment(
            "keep_this190.txt"
        )

        first_name = first.file.name
        first_storage = first.file.storage

        second_name = second.file.name
        second_storage = second.file.storage

        with self.captureOnCommitCallbacks(
            execute=True
        ):
            first.delete()

        self.assertFalse(
            first_storage.exists(first_name)
        )

        self.assertTrue(
            second_storage.exists(second_name)
        )

        self.assertTrue(
            MessageAttachment.objects.filter(
                pk=second.pk
            ).exists()
        )

    # =====================================
    # TEST 8 - DELETE VIEW USES ONE CALLBACK
    # =====================================

    def test_delete_view_uses_single_cleanup(self):

        attachment = self.create_attachment(
            "delete_view190.txt"
        )

        attachment_id = attachment.pk

        storage = attachment.file.storage
        filename = attachment.file.name

        self.client.force_login(self.staff)

        url = reverse(
            "message_attachment_delete",
            kwargs={"pk": attachment_id}
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            302
        )

        # One signal = one cleanup callback.
        self.assertEqual(len(callbacks), 1)

        self.assertFalse(
            MessageAttachment.objects.filter(
                pk=attachment_id
            ).exists()
        )

        self.assertFalse(storage.exists(filename))
