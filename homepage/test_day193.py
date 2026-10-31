
# ============================================
# DAY 193 - ADVANCED SEARCH, FILTER & SORT TESTS
# ============================================

from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, MessageAttachment


class AttachmentAdvancedSearchTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.temp_directory = TemporaryDirectory()

        cls.media_override = override_settings(
            MEDIA_ROOT=cls.temp_directory.name
        )
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.temp_directory.cleanup()
        super().tearDownClass()

    def setUp(self):
        User = get_user_model()

        self.staff = User.objects.create_user(
            username="day193_staff",
            password="TestPass123!",
            is_staff=True,
        )

        self.regular_user = User.objects.create_user(
            username="day193_regular",
            password="TestPass123!",
        )

        self.message = ContactMessage.objects.create(
            name="Day 193 User",
            email="day193@example.com",
            message="Advanced dashboard test",
        )

        self.pdf = self.create_attachment(
            "python_guide.pdf",
            b"PDF test content",
        )

        self.txt = self.create_attachment(
            "django_notes.txt",
            b"Text file test content",
        )

        self.jpg = self.create_attachment(
            "sample_photo.jpg",
            b"Image test content",
        )

        self.url = reverse("attachment_dashboard")

    def create_attachment(self, filename, content):
        uploaded_file = SimpleUploadedFile(
            filename,
            content,
        )

        return MessageAttachment.objects.create(
            contact_message=self.message,
            file=uploaded_file,
        )

    def get_result_ids(self, response):
        """
        Return attachment IDs actually displayed
        in the dashboard response.
        """
        return {
            attachment.pk
            for attachment in response.context["attachments"]
        }

    # ========================================
    # ACCESS CONTROL
    # ========================================

    def test_staff_can_access_dashboard(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_guest_cannot_access_dashboard(self):
        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)

    def test_regular_user_cannot_access_dashboard(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)

    # ========================================
    # SEARCH TEST
    # ========================================

    def test_search_finds_matching_filename(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"q": "python"},
        )

        self.assertEqual(response.status_code, 200)

        result_ids = self.get_result_ids(response)

        self.assertEqual(
            result_ids,
            {self.pdf.pk},
        )

        # Verify the actual saved filename
        # appears in the rendered dashboard.
        self.assertContains(
            response,
            Path(self.pdf.file.name).name,
        )

    # ========================================
    # EXTENSION FILTER TESTS
    # ========================================

    def test_extension_filter_pdf(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"extension": ".pdf"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.get_result_ids(response),
            {self.pdf.pk},
        )

        self.assertContains(
            response,
            Path(self.pdf.file.name).name,
        )

    def test_extension_filter_txt(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"extension": ".txt"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.get_result_ids(response),
            {self.txt.pk},
        )

        self.assertContains(
            response,
            Path(self.txt.file.name).name,
        )

    # ========================================
    # COMBINED SEARCH AND FILTER
    # ========================================

    def test_combined_search_and_extension(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {
                "q": "python",
                "extension": ".pdf",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            self.get_result_ids(response),
            {self.pdf.pk},
        )

    # ========================================
    # SORTING TESTS
    # ========================================

    def test_sort_oldest_first(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"sort": "oldest"},
        )

        self.assertEqual(response.status_code, 200)

        attachments = list(
            response.context["attachments"]
        )

        self.assertEqual(
            attachments[0].pk,
            self.pdf.pk,
        )

    def test_sort_filename_ascending(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"sort": "filename"},
        )

        self.assertEqual(response.status_code, 200)

        attachments = list(
            response.context["attachments"]
        )

        filenames = [
            attachment.file.name
            for attachment in attachments
        ]

        self.assertEqual(
            filenames,
            sorted(filenames),
        )

    def test_sort_largest_first(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            self.url,
            {"sort": "size_desc"},
        )

        self.assertEqual(response.status_code, 200)

        attachments = list(
            response.context["attachments"]
        )

        sizes = [
            attachment.file.size
            for attachment in attachments
        ]

        self.assertEqual(
            sizes,
            sorted(sizes, reverse=True),
        )
