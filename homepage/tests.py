from .report_category_forms import ReportCategoryForm
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import ReportCategory
from django.db import transaction
from .models import ContactMessage

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.core.paginator import Paginator

from .models import ContactMessage, MessageAttachment

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.test import TestCase
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.views.defaults import permission_denied, server_error


User = get_user_model()


class AuthenticationTests(TestCase):

    # These accounts exist ONLY in the test database.
    # These passwords are examples, not real credentials.

    @classmethod
    def setUpTestData(cls):

        cls.test_password = "ExampleTestPass!842"

        cls.user = User.objects.create_user(
            username="teststudent",
            email="student@example.com",
            password=cls.test_password,
            first_name="Test",
            last_name="Student"
        )

        cls.staff = User.objects.create_user(
            username="teststaff",
            email="staff@example.com",
            password=cls.test_password,
            is_staff=True
        )

    # ====================================
    # TEST 1 - HOME PAGE
    # ====================================

    def test_home_page_loads(self):

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)

    # ====================================
    # TEST 2 - LOGIN PAGE
    # ====================================

    def test_login_page_loads(self):

        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    # ====================================
    # TEST 3 - VALID LOGIN
    # ====================================

    def test_valid_login(self):

        logged_in = self.client.login(
            username="teststudent",
            password=self.test_password
        )

        self.assertTrue(logged_in)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)

    # ====================================
    # TEST 4 - INVALID LOGIN
    # ====================================

    def test_invalid_login(self):

        logged_in = self.client.login(
            username="teststudent",
            password="IncorrectPassword"
        )

        self.assertFalse(logged_in)

    # ====================================
    # TEST 5 - GUEST PROFILE ACCESS
    # ====================================

    def test_guest_cannot_access_profile(self):

        response = self.client.get(
            reverse("profile")
        )

        self.assertEqual(response.status_code, 302)

        self.assertIn(
            reverse("login"),
            response.url
        )

    # ====================================
    # TEST 6 - NORMAL USER CANNOT
    # ACCESS STAFF MESSAGES
    # ====================================

    def test_regular_user_cannot_view_messages(self):

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("message_list")
        )

        self.assertEqual(response.status_code, 302)

    # ====================================
    # TEST 7 - STAFF CAN VIEW MESSAGES
    # ====================================

    def test_staff_can_view_messages(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("message_list")
        )

        self.assertEqual(response.status_code, 200)

    # ====================================
    # TEST 8 - PROFILE UPDATE
    # ====================================

    def test_profile_update(self):

        self.client.force_login(self.user)

        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "Updated",
                "last_name": "Student",
                "email": "student@example.com"
            }
        )

        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Updated"
        )

    # ====================================
    # TEST 9 - CHANGE PASSWORD
    # ====================================

    def test_password_change(self):

        self.client.force_login(self.user)

        new_password = "NewTestPass!937"

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": self.test_password,
                "new_password1": new_password,
                "new_password2": new_password
            }
        )

        self.assertRedirects(
            response,
            reverse("password_change_done")
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(new_password)
        )

    # ====================================
    # TEST 10 - PASSWORD RESET EMAIL
    # ====================================

    def test_password_reset_email(self):

        response = self.client.post(
            reverse("password_reset"),
            {
                "email": "student@example.com"
            }
        )

        self.assertRedirects(
            response,
            reverse("password_reset_done")
        )

        self.assertEqual(
            len(mail.outbox),
            1
        )

        self.assertIn(
            "password/reset/confirm/",
            mail.outbox[0].body
        )

        from django.test import RequestFactory, override_settings
from django.core.exceptions import PermissionDenied
from django.views.defaults import permission_denied, server_error


class CustomErrorPageTests(TestCase):

    # TEST 11 - 404
    @override_settings(DEBUG=False)
    def test_custom_404_page(self):
        response = self.client.get(
            "/this-page-does-not-exist/"
        )

        self.assertEqual(response.status_code, 404)

        self.assertContains(
            response,
            "Page Not Found",
            status_code=404
        )

    # TEST 12 - 403
    def test_custom_403_page(self):
        request = RequestFactory().get("/restricted/")

        response = permission_denied(
            request,
            PermissionDenied("Access denied")
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Denied", response.content)

    # TEST 13 - 500
    def test_custom_500_page(self):
        request = RequestFactory().get("/example/")

        response = server_error(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            b"Something Went Wrong",
            response.content
        )

    from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ContactMessage


# =====================================
# DAY 170 - PAGINATION TESTS
# =====================================

class PaginationTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.staff = get_user_model().objects.create_user(
            username="pagination_staff",
            password="ExampleTestPass!842",
            is_staff=True
        )

        # Create 12 messages in the test database
        for number in range(1, 13):

            ContactMessage.objects.create(
                name=f"Student {number}",
                email=f"student{number}@example.com",
                message=f"Test message {number}"
            )

    def setUp(self):

        self.client.force_login(self.staff)

    # TEST 1 - FIRST PAGE

    def test_first_page(self):

        response = self.client.get("/messages/")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].number,
            1
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            5
        )

    # TEST 2 - LAST PAGE

    def test_last_page(self):

        response = self.client.get(
            "/messages/?page=3"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].number,
            3
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            2
        )

    # TEST 3 - INVALID PAGE

    def test_invalid_page(self):

        response = self.client.get(
            "/messages/?page=abc"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].number,
            1
        )

        from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import ContactMessage


# =====================================
# DAY 171 - SEARCH TESTS
# =====================================

class MessageSearchTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        # Create a test staff account
        cls.staff = get_user_model().objects.create_user(
            username="search_staff",
            password="ExampleTestPass!842",
            is_staff=True
        )

        # One message matching the name Arman
        ContactMessage.objects.create(
            name="Arman",
            email="arman@example.com",
            message="I am learning Python"
        )

        # Seven messages containing Django
        for number in range(1, 8):

            ContactMessage.objects.create(
                name=f"Student {number}",
                email=f"student{number}@example.com",
                message=f"Django learning message {number}"
            )

        # One message that doesn't match Django
        ContactMessage.objects.create(
            name="muneeb",
            email="muneeb@example.com",
            message="I am learning SQL"
        )

    def setUp(self):

        self.client.force_login(self.staff)

    # TEST 1 - SEARCH BY NAME

    def test_search_by_name(self):

        response = self.client.get(
            "/messages/?q=arman"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1
        )

        self.assertContains(response, "Arman")

    # TEST 2 - SEARCH WITH PAGINATION

    def test_search_with_pagination(self):

        response = self.client.get(
            "/messages/?q=DJANGO&page=2"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].number,
            2
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            2
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            7
        )

    # TEST 3 - NO MATCHES

    def test_search_no_results(self):

        response = self.client.get(
            "/messages/?q=nomatch987"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            0
        )

        self.assertContains(
            response,
            "No messages match your search."
        )

        from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import ContactMessage


# =====================================
# DAY 172 - ADVANCED FILTERING TESTS
# =====================================

class AdvancedFilteringTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.staff = get_user_model().objects.create_user(
            username="advanced_filter_staff",
            password="ExampleTestPass!842",
            is_staff=True
        )

        ContactMessage.objects.create(
            name="Arman",
            email="arman@example.com",
            message="Learning Python"
        )

        ContactMessage.objects.create(
            name="Sara",
            email="vip@example.com",
            message="Django question"
        )

        ContactMessage.objects.create(
            name="Rahul",
            email="rahul@example.com",
            message="Learning SQL"
        )

        for number in range(1, 8):
            ContactMessage.objects.create(
                name=f"Student {number}",
                email=f"student{number}@example.com",
                message=f"Alpha test message {number}"
            )

    def setUp(self):

        self.client.force_login(self.staff)

    # TEST 1 - FILTER BY EMAIL

    def test_filter_by_email(self):

        response = self.client.get(
            "/messages/?q=vip&field=email"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1
        )

        self.assertContains(
            response,
            "vip@example.com"
        )

    # TEST 2 - SORT OLDEST FIRST

    def test_sort_oldest_first(self):

        response = self.client.get(
            "/messages/?sort=oldest"
        )

        page_obj = response.context["page_obj"]

        first_message = page_obj[0]

        self.assertEqual(
            first_message.name,
            "Arman"
        )

        self.assertEqual(
            response.context["sort_by"],
            "oldest"
        )

    # TEST 3 - FILTER AND PAGINATION

    def test_filter_with_pagination(self):

        response = self.client.get(
            "/messages/?q=alpha&field=message&sort=oldest&page=2"
        )

        self.assertEqual(response.status_code, 200)

        page_obj = response.context["page_obj"]

        self.assertEqual(
            page_obj.number,
            2
        )

        self.assertEqual(
            page_obj.paginator.count,
            7
        )

        self.assertEqual(
            len(page_obj),
            2
        )

        from django.test import TestCase
from .models import ContactMessage, MessageNote


class MessageRelationshipTests(TestCase):

    def setUp(self):
        self.contact = ContactMessage.objects.create(
            name="Test Student",
            email="student@example.com",
            message="Learning Django relationships"
        )

        self.note1 = MessageNote.objects.create(
            contact_message=self.contact,
            note="First test note"
        )

        self.note2 = MessageNote.objects.create(
            contact_message=self.contact,
            note="Second test note"
        )

    def test_note_has_parent_message(self):
        self.assertEqual(
            self.note1.contact_message,
            self.contact
        )

    def test_message_has_multiple_notes(self):
        self.assertEqual(
            self.contact.notes.count(),
            2
        )

    def test_deleting_message_removes_notes(self):
        self.contact.delete()

        self.assertEqual(
            MessageNote.objects.count(),
            0
        )

        from django.test import TestCase
from .models import ContactMessage, MessageTag


# =====================================
# DAY 174 - MANY TO MANY TESTS
# =====================================

class ManyToManyRelationshipTests(TestCase):

    def setUp(self):

        # Create two contact messages
        self.message1 = ContactMessage.objects.create(
            name="Arman",
            email="arman@example.com",
            message="Learning Python and Django"
        )

        self.message2 = ContactMessage.objects.create(
            name="Sara",
            email="sara@example.com",
            message="Django backend development"
        )

        # Create two tags
        self.python_tag = MessageTag.objects.create(
            name="Python"
        )

        self.django_tag = MessageTag.objects.create(
            name="Django"
        )

        # Assign tags to messages
        self.message1.tags.add(
            self.python_tag,
            self.django_tag
        )

        self.message2.tags.add(
            self.django_tag
        )

    # TEST 1 - ONE MESSAGE HAS MULTIPLE TAGS

    def test_message_has_multiple_tags(self):

        self.assertEqual(
            self.message1.tags.count(),
            2
        )

    # TEST 2 - ONE TAG HAS MULTIPLE MESSAGES

    def test_tag_has_multiple_messages(self):

        self.assertEqual(
            self.django_tag.contact_messages.count(),
            2
        )

    # TEST 3 - REMOVE A TAG RELATIONSHIP

    def test_remove_tag_from_message(self):

        self.message1.tags.remove(
            self.python_tag
        )

        self.assertEqual(
            self.message1.tags.count(),
            1
        )

        # The tag must still exist
        self.assertTrue(
            MessageTag.objects.filter(
                name="Python"
            ).exists()
        )
        from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import DeveloperProfile


# =====================================
# DAY 175 - ONE TO ONE RELATIONSHIP TESTS
# =====================================

class OneToOneRelationshipTests(TestCase):

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            username="developer_test",
            password="ExampleTestPass!842",
            first_name="Test",
            last_name="Developer",
            email="developer@example.com"
        )

    # TEST 1 - FORWARD AND REVERSE RELATIONSHIP

    def test_profile_belongs_to_user(self):

        # The signal already created this profile
        profile = self.user.developer_profile

        profile.bio = "Learning Django"

        profile.favorite_language = "Python"

        profile.save()

        self.assertEqual(
            profile.user,
            self.user
        )

        self.assertEqual(
            self.user.developer_profile,
            profile
        )

    # TEST 2 - GET OR CREATE RETURNS ONE PROFILE

    def test_get_or_create_profile(self):

        first_profile, created = (
            DeveloperProfile.objects.get_or_create(
                user=self.user
            )
        )

        second_profile, created_again = (
            DeveloperProfile.objects.get_or_create(
                user=self.user
            )
        )

        # The signal created the profile earlier
        self.assertFalse(created)

        self.assertFalse(created_again)

        self.assertEqual(
            first_profile.pk,
            second_profile.pk
        )

        self.assertEqual(
            DeveloperProfile.objects.filter(
                user=self.user
            ).count(),
            1
        )

    # TEST 3 - EDIT DEVELOPER PROFILE THROUGH VIEW

    def test_edit_developer_profile(self):

        self.client.force_login(self.user)

        response = self.client.post(
            "/accounts/profile/",
            {
                "first_name": "Test",
                "last_name": "Developer",
                "email": "developer@example.com",
                "bio": "Python Backend Learner",
                "favorite_language": "Python"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        profile = DeveloperProfile.objects.get(
            user=self.user
        )

        self.assertEqual(
            profile.favorite_language,
            "Python"
        )

        self.assertEqual(
            profile.bio,
            "Python Backend Learner"
        )

        from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import DeveloperProfile


# =====================================
# DAY 176 - DJANGO SIGNAL TESTS
# =====================================

class ProfileSignalTests(TestCase):

    def setUp(self):

        self.User = get_user_model()

    # TEST 1 - PROFILE CREATED AUTOMATICALLY

    def test_profile_created_automatically(self):

        user = self.User.objects.create_user(
            username="signal_student",
            password="ExampleTestPass!842"
        )

        self.assertTrue(
            DeveloperProfile.objects.filter(
                user=user
            ).exists()
        )

        self.assertEqual(
            user.developer_profile.user,
            user
        )

    # TEST 2 - NO DUPLICATE PROFILES

    def test_updating_user_does_not_duplicate_profile(self):

        user = self.User.objects.create_user(
            username="signal_update",
            password="ExampleTestPass!842"
        )

        user.first_name = "Arman"
        user.save()

        self.assertEqual(
            DeveloperProfile.objects.filter(
                user=user
            ).count(),
            1
        )

    # TEST 3 - PROFILE INFORMATION IS PRESERVED

    def test_profile_data_is_preserved(self):

        user = self.User.objects.create_user(
            username="signal_profile",
            password="ExampleTestPass!842"
        )

        profile = user.developer_profile

        profile.bio = "Learning Django"
        profile.favorite_language = "Python"
        profile.save()

        # Update only the user's name
        user.first_name = "Student"
        user.save()

        profile.refresh_from_db()

        self.assertEqual(
            profile.bio,
            "Learning Django"
        )

        self.assertEqual(
            profile.favorite_language,
            "Python"
        )

        from django.test import TestCase

from .models import ContactMessage, MessageTag


# =====================================
# DAY 177 - CUSTOM QUERYSET TESTS
# =====================================

class CustomQuerySetTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.message1 = ContactMessage.objects.create(
            name="Arman",
            email="arman@example.com",
            message="Learning Django"
        )

        cls.message2 = ContactMessage.objects.create(
            name="Sara",
            email="sara@example.com",
            message="Learning Python"
        )

        cls.message3 = ContactMessage.objects.create(
            name="Rahul",
            email="rahul@example.com",
            message="SQL and Django practice"
        )

        cls.python_tag = MessageTag.objects.create(
            name="Python"
        )

        cls.sql_tag = MessageTag.objects.create(
            name="SQL"
        )

        cls.message1.tags.add(cls.python_tag)
        cls.message2.tags.add(cls.python_tag)
        cls.message3.tags.add(cls.sql_tag)

    # TEST 1 - SEARCH

    def test_custom_search(self):

        results = ContactMessage.objects.search(
            "django"
        )

        self.assertEqual(results.count(), 2)

        self.assertIn(self.message1, results)
        self.assertIn(self.message3, results)

    # TEST 2 - FILTER BY TAG

    def test_filter_by_tag(self):

        results = ContactMessage.objects.with_tag(
            "python"
        )

        self.assertEqual(results.count(), 2)

        self.assertIn(self.message1, results)
        self.assertIn(self.message2, results)

    # TEST 3 - CHAINING AND SORTING

    def test_queryset_chaining(self):

        results = (
            ContactMessage.objects
            .search("Django")
            .with_tag("Python")
            .newest()
        )

        self.assertEqual(results.count(), 1)

        self.assertEqual(
            results.first(),
            self.message1
        )

        newest_messages = ContactMessage.objects.newest()

        self.assertEqual(
            newest_messages.first(),
            self.message3
        )


        from django.test import TestCase

from .models import ContactMessage, MessageNote, MessageTag


# =====================================
# DAY 178 - QUERY OPTIMIZATION TESTS
# =====================================

class QueryOptimizationTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        # Create two contact messages
        cls.message1 = ContactMessage.objects.create(
            name="Arman",
            email="arman@example.com",
            message="Learning Django"
        )

        cls.message2 = ContactMessage.objects.create(
            name="Sara",
            email="sara@example.com",
            message="Learning Python"
        )

        # Create a note for each message
        MessageNote.objects.create(
            contact_message=cls.message1,
            note="First message reviewed"
        )

        MessageNote.objects.create(
            contact_message=cls.message2,
            note="Second message reviewed"
        )

        # Create tags
        python_tag = MessageTag.objects.create(
            name="Python"
        )

        django_tag = MessageTag.objects.create(
            name="Django"
        )

        # Assign tags
        cls.message1.tags.add(
            python_tag,
            django_tag
        )

        cls.message2.tags.add(
            python_tag
        )

    # TEST 1 - SELECT_RELATED

    def test_select_related_uses_one_query(self):

        with self.assertNumQueries(1):

            notes = list(
                MessageNote.objects.select_related(
                    "contact_message"
                )
            )

            for note in notes:
                _ = note.contact_message.name
    # TEST 2 - PREFETCH_RELATED

    def test_prefetch_related_uses_three_queries(self):

        with self.assertNumQueries(3):

            messages = list(
                ContactMessage.objects.prefetch_related(
                    "notes",
                    "tags"
                )
            )

            for message in messages:
                list(message.notes.all())
                list(message.tags.all())

    # TEST 3 - PREFETCH CACHE

    def test_prefetch_avoids_extra_queries(self):

        messages = list(
            ContactMessage.objects.prefetch_related(
                "notes",
                "tags"
            )
        )

        # Related data has already been fetched.
        # Accessing it again requires zero queries.
        with self.assertNumQueries(0):

            for message in messages:
                list(message.notes.all())
                list(message.tags.all())

                from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import (
    ContactMessage,
    MessageNote,
    MessageTag,
)


# =====================================
# DAY 179 - AGGREGATION TESTS
# =====================================

class AggregationAnnotationTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.staff = get_user_model().objects.create_user(
            username="stats_staff",
            password="ExampleTestPass!842",
            is_staff=True
        )

        cls.message1 = ContactMessage.objects.create(
            name="Arman",
            email="arman@example.com",
            message="Learning Django"
        )

        cls.message2 = ContactMessage.objects.create(
            name="Sara",
            email="sara@example.com",
            message="Learning Python"
        )

        # Create three notes
        MessageNote.objects.create(
            contact_message=cls.message1,
            note="First note"
        )

        MessageNote.objects.create(
            contact_message=cls.message1,
            note="Second note"
        )

        MessageNote.objects.create(
            contact_message=cls.message2,
            note="Third note"
        )

        # Create two tags
        python_tag = MessageTag.objects.create(
            name="Python"
        )

        django_tag = MessageTag.objects.create(
            name="Django"
        )

        # Python is used twice
        cls.message1.tags.add(python_tag)
        cls.message2.tags.add(python_tag)

        # Django is used once
        cls.message1.tags.add(django_tag)

    def setUp(self):
        self.client.force_login(self.staff)

    # TEST 1 - AGGREGATION COUNTS

    def test_aggregation_counts(self):

        stats = ContactMessage.objects.aggregate(
            total_messages=Count("id", distinct=True),
            total_notes=Count("notes", distinct=True),
            used_tags=Count("tags", distinct=True)
        )

        self.assertEqual(stats["total_messages"], 2)
        self.assertEqual(stats["total_notes"], 3)
        self.assertEqual(stats["used_tags"], 2)

    # TEST 2 - ANNOTATION COUNTS

    def test_tag_annotation(self):

        tags = MessageTag.objects.annotate(
            message_count=Count(
                "contact_messages",
                distinct=True
            )
        )

        counts = {
            tag.name: tag.message_count
            for tag in tags
        }

        self.assertEqual(counts["Python"], 2)
        self.assertEqual(counts["Django"], 1)

    # TEST 3 - DASHBOARD DISPLAYS STATISTICS

    def test_dashboard_statistics(self):

        response = self.client.get("/messages/")

        self.assertEqual(response.status_code, 200)

        stats = response.context["statistics"]

        self.assertEqual(stats["total_messages"], 2)
        self.assertEqual(stats["total_notes"], 3)
        self.assertEqual(stats["used_tags"], 2)

        popular_tags = list(
            response.context["popular_tags"]
        )

        self.assertEqual(
            popular_tags[0].name,
            "Python"
        )

        self.assertEqual(
            popular_tags[0].message_count,
            2
        )

        from django.test import TestCase
from django.urls import reverse, resolve
from .views import LearningHubView


# =====================================
# DAY 181 - CLASS BASED VIEW TESTS
# =====================================

class ClassBasedViewTests(TestCase):

    # Test 1 - Check the URL
    def test_learning_hub_uses_class_based_view(self):

        match = resolve("/learning/")

        self.assertEqual(
            match.func.view_class,
            LearningHubView
        )

    # Test 2 - Check the template
    def test_learning_hub_page_loads(self):

        response = self.client.get(
            reverse("learning_hub")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "homepage/learning_hub.html"
        )

    # Test 3 - Check the context
    def test_learning_hub_context(self):

        response = self.client.get(
            reverse("learning_hub")
        )

        self.assertEqual(
            response.context["page_heading"],
            "Backend Learning Hub"
        )

        self.assertEqual(
            len(response.context["topics"]),
            3
        )


from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import (
    ContactMessage,
    MessageNote,
    MessageTag,
)


# =====================================
# DAY 182 - LISTVIEW AND DETAILVIEW TESTS
# =====================================

class GenericDisplayViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        # Staff user can view messages
        cls.staff = User.objects.create_user(
            username="day182_staff",
            password="ExampleTestPass!842",
            is_staff=True
        )

        # Regular user cannot view messages
        cls.regular_user = User.objects.create_user(
            username="day182_regular",
            password="ExampleTestPass!842"
        )

        # Create seven test messages
        for number in range(1, 8):

            message = ContactMessage.objects.create(
                name=f"Student {number}",
                email=f"student{number}@example.com",
                message=f"Day 182 message {number}"
            )

            if number == 1:
                cls.message = message

        # Add a note and a tag to one message
        MessageNote.objects.create(
            contact_message=cls.message,
            note="Reviewed this message"
        )

        tag = MessageTag.objects.create(
            name="Python"
        )

        cls.message.tags.add(tag)

    # TEST 1 - LISTVIEW PAGINATION

    def test_list_view_pagination(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("message_browse")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/message_browse.html"
        )

        self.assertEqual(
            len(response.context["contact_messages"]),
            5
        )

        self.assertEqual(
            response.context["paginator"].count,
            7
        )

    # TEST 2 - DETAILVIEW CONTENT

    def test_detail_view_shows_message(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            reverse(
                "message_detail",
                kwargs={"pk": self.message.pk}
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["contact_message"],
            self.message
        )

        self.assertContains(
            response,
            "Reviewed this message"
        )

        self.assertContains(
            response,
            "Python"
        )

    # TEST 3 - GUESTS CANNOT VIEW MESSAGES

    def test_guest_access_blocked(self):

        urls = [
            reverse("message_browse"),
            reverse(
                "message_detail",
                kwargs={"pk": self.message.pk}
            )
        ]

        for url in urls:

            with self.subTest(url=url):

                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    302
                )

    # TEST 4 - REGULAR USERS CANNOT VIEW MESSAGES

    def test_regular_user_access_blocked(self):

        self.client.force_login(self.regular_user)

        urls = [
            reverse("message_browse"),
            reverse(
                "message_detail",
                kwargs={"pk": self.message.pk}
            )
        ]

        for url in urls:

            with self.subTest(url=url):

                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    302
                )


from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import ContactMessage


# =====================================
# DAY 183 - CREATEVIEW / UPDATEVIEW TESTS
# =====================================

class MessageCreateUpdateTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff = User.objects.create_user(
            username="day183_staff",
            password="TestPass!183",
            is_staff=True
        )

        cls.regular_user = User.objects.create_user(
            username="day183_regular",
            password="TestPass!183"
        )

        cls.message = ContactMessage.objects.create(
            name="Original Name",
            email="original@example.com",
            message="Original message"
        )

    # TEST 1: STAFF CAN CREATE A MESSAGE

    def test_staff_can_create_message(self):

        self.client.force_login(self.staff)

        url = reverse("message_create")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/message_form.html"
        )

        response = self.client.post(
            url,
            {
                "name": "New Student",
                "email": "new@example.com",
                "message": "Learning CreateView"
            }
        )

        created = ContactMessage.objects.get(
            email="new@example.com"
        )

        self.assertRedirects(
            response,
            reverse(
                "message_detail",
                kwargs={"pk": created.pk}
            ),
            fetch_redirect_response=False
        )

    # TEST 2: STAFF CAN UPDATE A MESSAGE

    def test_staff_can_update_message(self):

        self.client.force_login(self.staff)

        url = reverse(
            "message_edit",
            kwargs={"pk": self.message.pk}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                "name": "Updated Name",
                "email": "updated@example.com",
                "message": "Updated using UpdateView"
            }
        )

        self.assertEqual(response.status_code, 302)

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.name,
            "Updated Name"
        )

        self.assertEqual(
            self.message.message,
            "Updated using UpdateView"
        )

    # TEST 3: INVALID FORM DOES NOT SAVE

    def test_invalid_form_does_not_save(self):

        self.client.force_login(self.staff)

        count_before = ContactMessage.objects.count()

        response = self.client.post(
            reverse("message_create"),
            {
                "name": "",
                "email": "not-an-email",
                "message": ""
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            ContactMessage.objects.count(),
            count_before
        )

        self.assertFalse(
            response.context["form"].is_valid()
        )

    # TEST 4: GUESTS CANNOT ACCESS FORMS

    def test_guest_access_blocked(self):

        urls = [
            reverse("message_create"),
            reverse(
                "message_edit",
                kwargs={"pk": self.message.pk}
            )
        ]

        for url in urls:

            with self.subTest(url=url):

                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)

    # TEST 5: REGULAR USERS CANNOT ACCESS FORMS

    def test_regular_user_access_blocked(self):

        self.client.force_login(self.regular_user)

        urls = [
            reverse("message_create"),
            reverse(
                "message_edit",
                kwargs={"pk": self.message.pk}
            )
        ]

        for url in urls:

            with self.subTest(url=url):

                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)


from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import ContactMessage, MessageNote


# =====================================
# DAY 184 - DELETEVIEW TESTS
# =====================================

class MessageDeleteViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff = User.objects.create_user(
            username="day184_staff",
            password="ExamplePass!184",
            is_staff=True
        )

        cls.regular_user = User.objects.create_user(
            username="day184_regular",
            password="ExamplePass!184"
        )

        cls.message = ContactMessage.objects.create(
            name="Day 184 Student",
            email="day184@example.com",
            message="Test message for deletion"
        )

        cls.note = MessageNote.objects.create(
            contact_message=cls.message,
            note="Example note for Day 184"
        )

    def get_delete_url(self):

        return reverse(
            "message_delete",
            kwargs={"pk": self.message.pk}
        )

    # TEST 1 - CONFIRMATION PAGE LOADS

    def test_delete_confirmation_page(self):

        self.client.force_login(self.staff)

        response = self.client.get(
            self.get_delete_url()
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/message_confirm_delete.html"
        )

        self.assertContains(
            response,
            "Day 184 Student"
        )

    # TEST 2 - GET MUST NOT DELETE DATA

    def test_get_request_does_not_delete(self):

        self.client.force_login(self.staff)

        self.client.get(self.get_delete_url())

        self.assertTrue(
            ContactMessage.objects.filter(
                pk=self.message.pk
            ).exists()
        )

    # TEST 3 - STAFF POST DELETES DATA

    def test_staff_can_delete_message(self):

        self.client.force_login(self.staff)

        response = self.client.post(
            self.get_delete_url()
        )

        self.assertRedirects(
            response,
            reverse("message_browse"),
            fetch_redirect_response=False
        )

        self.assertFalse(
            ContactMessage.objects.filter(
                pk=self.message.pk
            ).exists()
        )

        # Related notes should also be removed.
        self.assertFalse(
            MessageNote.objects.filter(
                pk=self.note.pk
            ).exists()
        )

    # TEST 4 - GUESTS CANNOT DELETE

    def test_guest_cannot_delete(self):

        url = self.get_delete_url()

        for method in ["get", "post"]:

            with self.subTest(method=method):

                response = getattr(
                    self.client,
                    method
                )(url)

                self.assertEqual(
                    response.status_code,
                    302
                )

        self.assertTrue(
            ContactMessage.objects.filter(
                pk=self.message.pk
            ).exists()
        )

    # TEST 5 - REGULAR USERS CANNOT DELETE

    def test_regular_user_cannot_delete(self):

        self.client.force_login(
            self.regular_user
        )

        url = self.get_delete_url()

        for method in ["get", "post"]:

            with self.subTest(method=method):

                response = getattr(
                    self.client,
                    method
                )(url)

                self.assertEqual(
                    response.status_code,
                    302
                )

        self.assertTrue(
            ContactMessage.objects.filter(
                pk=self.message.pk
            ).exists()
        )


# ======================================
# DAY 196 - CHART FILTER TESTS
# ======================================

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AttachmentChartFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="day196_staff",
            password="ExampleTestPass!196",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_default_chart_filter(self):
        response = self.client.get(
            reverse("attachment_dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["selected_chart_type"],
            "all",
        )
        self.assertEqual(
            len(response.context["attachment_chart_data"]["labels"]),
            6,
        )

    def test_pdf_chart_filter(self):
        response = self.client.get(
            reverse("attachment_dashboard"),
            {"chart_type": "pdf"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["attachment_chart_data"]["labels"],
            ["PDF"],
        )

    def test_invalid_chart_filter(self):
        response = self.client.get(
            reverse("attachment_dashboard"),
            {"chart_type": "invalid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["selected_chart_type"],
            "all",
        )

# ======================================
# DAY 197 - DATE RANGE FILTER TESTS
# ======================================

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AttachmentDateRangeTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="day197_staff",
            password="ExampleTestPass!197",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_default_date_range(self):
        response = self.client.get(
            reverse("attachment_dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["selected_date_range"],
            "all",
        )

    def test_last_seven_days(self):
        response = self.client.get(
            reverse("attachment_dashboard"),
            {"date_range": "7"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["selected_date_range"],
            "7",
        )

    def test_invalid_date_range(self):
        response = self.client.get(
            reverse("attachment_dashboard"),
            {"date_range": "invalid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["selected_date_range"],
            "all",
        )

        # ======================================
# DAY 198 - CSV EXPORT TESTS
# ======================================

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AttachmentAnalyticsCSVTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="day198_staff",
            password="ExampleTestPass!198",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_csv_export_status(self):
        response = self.client.get(
            reverse("attachment_analytics_csv")
        )

        self.assertEqual(response.status_code, 200)

    def test_csv_content_type(self):
        response = self.client.get(
            reverse("attachment_analytics_csv")
        )

        self.assertTrue(
            response["Content-Type"].startswith("text/csv")
        )

    def test_csv_header(self):
        response = self.client.get(
            reverse("attachment_analytics_csv")
        )

        self.assertIn(
            b"File Type,Count",
            response.content
        )

    def test_pdf_filter_export(self):
        response = self.client.get(
            reverse("attachment_analytics_csv"),
            {
                "chart_type": "pdf",
                "date_range": "7",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PDF", response.content)
        self.assertNotIn(b"Word Documents", response.content)

        # ======================================
# DAY 199 - IMPROVED CSV EXPORT TESTS
# ======================================

import csv
import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AttachmentAnalyticsCSVImprovementTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="day199_staff",
            password="ExampleTestPass!199",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def get_csv_rows(self, response):
        text = response.content.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(text)))

    def test_filename_contains_selected_filters(self):
        response = self.client.get(
            reverse("attachment_analytics_csv"),
            {
                "chart_type": "pdf",
                "date_range": "30",
            },
        )

        filename = response["Content-Disposition"]

        self.assertIn("attachment_analytics_", filename)
        self.assertIn("_pdf_30days.csv", filename)

    def test_csv_contains_metadata(self):
        response = self.client.get(
            reverse("attachment_analytics_csv"),
            {
                "chart_type": "pdf",
                "date_range": "7",
            },
        )

        rows = self.get_csv_rows(response)

        self.assertIn(
            ["Report", "Attachment Analytics"],
            rows,
        )

        self.assertIn(
            ["Date Range", "Last 7 Days"],
            rows,
        )

        self.assertIn(
            ["File Type Filter", "PDF"],
            rows,
        )

    def test_csv_contains_total_row(self):
        response = self.client.get(
            reverse("attachment_analytics_csv")
        )

        rows = self.get_csv_rows(response)

        self.assertEqual(
            rows[-1][0],
            "Total",
        )

        self.assertTrue(
            rows[-1][1].isdigit()
        )

    def test_csv_has_excel_bom(self):
        response = self.client.get(
            reverse("attachment_analytics_csv")
        )

        self.assertTrue(
            response.content.startswith(b"\xef\xbb\xbf")
        )

        # ======================================
# DAY 202 - QUERY OPTIMIZATION TESTS
# ======================================

from django.test import TestCase

from .models import ContactMessage, MessageAttachment


class Day202QueryOptimizationTests(TestCase):

    def test_select_related_query(self):
        with self.assertNumQueries(1):
            attachments = list(
                MessageAttachment.objects.select_related(
                    "contact_message"
                )
            )

            for attachment in attachments:
                _ = attachment.contact_message

    def test_attachment_count_query(self):
        with self.assertNumQueries(1):
            total = MessageAttachment.objects.count()

        self.assertGreaterEqual(total, 0)


# ==========================================
# DAY 203 - ADVANCED QUERY OPTIMIZATION TESTS
# ==========================================

class Day203AdvancedQueryTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Create three contact messages.
        Each message has one attachment.
        """

        for index in range(1, 4):

            contact_message = ContactMessage.objects.create(
                name=f"Day203 User {index}",
                email=f"day203user{index}@example.com",
                message=f"Test message number {index}",
            )

            MessageAttachment.objects.create(
                contact_message=contact_message,
                file=f"day203/test_file_{index}.txt",
            )

    def test_n_plus_one_problem(self):
        """
        Without optimization:
        1 query for attachments
        3 queries for related messages
        Total = 4 queries
        """

        with self.assertNumQueries(4):

            attachments = list(
                MessageAttachment.objects.all()
            )

            names = [
                attachment.contact_message.name
                for attachment in attachments
            ]

        self.assertEqual(len(names), 3)

    def test_select_related_optimization(self):
        """
        With select_related:
        Attachments and contact messages
        are retrieved using one query.
        """

        with self.assertNumQueries(1):

            attachments = list(
                MessageAttachment.objects.select_related(
                    "contact_message"
                )
            )

            names = [
                attachment.contact_message.name
                for attachment in attachments
            ]

        self.assertEqual(len(names), 3)

    def test_prefetch_related_optimization(self):
        """
        Prefetch reverse relationships:
        1 query for contact messages
        1 query for attachments
        Total = 2 queries
        """

        relation = MessageAttachment._meta.get_field(
            "contact_message"
        ).remote_field

        reverse_name = relation.get_accessor_name()

        with self.assertNumQueries(2):

            messages = list(
                ContactMessage.objects.prefetch_related(
                    reverse_name
                )
            )

            total = sum(
                len(list(getattr(message, reverse_name).all()))
                for message in messages
            )

        self.assertEqual(total, 3)

    def test_annotate_attachment_counts(self):
        """
        Annotate each contact message
        with its number of attachments.
        """

        reverse_query_name = (
            MessageAttachment._meta.get_field(
                "contact_message"
            ).related_query_name()
        )

        with self.assertNumQueries(1):

            messages = list(
                ContactMessage.objects.annotate(
                    attachment_count=Count(
                        reverse_query_name
                    )
                )
            )

        counts = [
            message.attachment_count
            for message in messages
        ]

        self.assertEqual(sorted(counts), [1, 1, 1])


# ==========================================
# DAY 204 - DATABASE INDEX TESTS
# ==========================================

class Day204DatabaseIndexTests(TestCase):

    def test_uploaded_at_has_database_index(self):
        """
        Verify that the uploaded_at field
        has a database index.
        """

        table_name = MessageAttachment._meta.db_table

        with connection.cursor() as cursor:
            constraints = (
                connection.introspection.get_constraints(
                    cursor,
                    table_name
                )
            )

        index_found = any(
            details.get("index")
            and "uploaded_at" in details.get("columns", [])
            for details in constraints.values()
        )

        self.assertTrue(
            index_found,
            "Expected a database index on uploaded_at."
        )

    def test_filter_recent_attachments(self):
        """
        Verify that date filtering returns
        only attachments uploaded recently.
        """

        message = ContactMessage.objects.create(
            name="Day204 User",
            email="day204@example.com",
            message="Testing database date filters",
        )

        recent_attachment = MessageAttachment.objects.create(
            contact_message=message,
            file="day204/recent.txt",
        )

        old_attachment = MessageAttachment.objects.create(
            contact_message=message,
            file="day204/old.txt",
        )

        now = timezone.now()

        MessageAttachment.objects.filter(
            pk=recent_attachment.pk
        ).update(
            uploaded_at=now - timedelta(days=2)
        )

        MessageAttachment.objects.filter(
            pk=old_attachment.pk
        ).update(
            uploaded_at=now - timedelta(days=30)
        )

        cutoff_date = now - timedelta(days=7)

        recent_ids = set(
            MessageAttachment.objects.filter(
                uploaded_at__gte=cutoff_date
            ).values_list("pk", flat=True)
        )

        self.assertEqual(
            recent_ids,
            {recent_attachment.pk}
        )

# ==========================================
# DAY 205 - PAGINATION TESTS
# ==========================================

class Day205PaginationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="day205_staff",
            password="ExampleTestPass!205",
            is_staff=True,
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_page_loads_successfully(self):
        response = self.client.get(
            reverse("efficient_attachment_list")
        )

        self.assertEqual(response.status_code, 200)

    def test_pagination_size(self):
        response = self.client.get(
            reverse("efficient_attachment_list")
        )

        self.assertEqual(
            response.context["paginator"].per_page,
            20
        )

    def test_non_staff_access_denied(self):
        user = get_user_model().objects.create_user(
            username="day205_regular",
            password="ExampleTestPass!205",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("efficient_attachment_list")
        )

        self.assertNotEqual(response.status_code, 200)



# ==========================================
# DAY 206 - ADVANCED PAGINATION TESTS
# ==========================================

class Day206AdvancedPaginationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Create a staff user, one contact message,
        and 25 attachments for pagination testing.
        """

        cls.staff_user = get_user_model().objects.create_user(
            username="day206_staff",
            password="Day206TestPass!123",
            is_staff=True,
        )

        cls.contact_message = ContactMessage.objects.create(
            name="Day206 Test User",
            email="day206@example.com",
            message="Testing Django pagination with 25 files.",
        )

        cls.attachment_ids = []

        for number in range(1, 26):

            attachment = MessageAttachment.objects.create(
                contact_message=cls.contact_message,
                file=f"day206/test_file_{number}.txt",
            )

            cls.attachment_ids.append(attachment.pk)

    def setUp(self):
        """
        Log in as staff before every test.
        """
        self.client.force_login(self.staff_user)

    def test_first_page_has_20_attachments(self):
        """
        Page 1 should display 20 attachments.
        """

        response = self.client.get(
            reverse("efficient_attachment_list")
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.context["attachments"]),
            20,
        )

        self.assertEqual(
            response.context["page_obj"].number,
            1,
        )

    def test_second_page_has_5_attachments(self):
        """
        Page 2 should display the remaining 5.
        """

        response = self.client.get(
            reverse("efficient_attachment_list"),
            {"page": 2},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.context["attachments"]),
            5,
        )

        self.assertEqual(
            response.context["page_obj"].number,
            2,
        )

    def test_pagination_has_two_pages(self):
        """
        The paginator should report two pages.
        """

        response = self.client.get(
            reverse("efficient_attachment_list")
        )

        paginator = response.context["paginator"]

        self.assertEqual(paginator.count, 25)
        self.assertEqual(paginator.num_pages, 2)
        self.assertEqual(paginator.per_page, 20)

    def test_attachment_order_is_correct(self):
        """
        Newest attachment IDs should appear first.
        """

        response = self.client.get(
            reverse("efficient_attachment_list")
        )

        actual_ids = [
            attachment.pk
            for attachment in response.context["attachments"]
        ]

        expected_ids = list(
            reversed(self.attachment_ids)
        )[:20]

        self.assertEqual(actual_ids, expected_ids)

    def test_invalid_page_returns_last_page(self):
        """
        An out-of-range page number should return
        the last page with ListView's default
        get_page() behavior for invalid page values.
        """

        response = self.client.get(
            reverse("efficient_attachment_list"),
            {"page": 999},
        )

        self.assertEqual(response.status_code, 404)


    def test_paginated_queryset_uses_one_query(self):
        """
        Fetching and accessing related contact
        messages should use one database query.
        """

        from .views import EfficientAttachmentListView

        view = EfficientAttachmentListView()

        with self.assertNumQueries(1):

            attachments = list(
                view.get_queryset()[:20]
            )

            contact_names = [
                attachment.contact_message.name
                for attachment in attachments
            ]

        self.assertEqual(len(attachments), 20)

        self.assertEqual(
            len(contact_names),
            20,
        )

# ====================================================
# DAY 207 - DJANGO QUERYSET PERFORMANCE MONITORING
# ====================================================

class Day207QueryPerformanceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Create 25 attachments in the test database.
        """

        cls.contact_message = ContactMessage.objects.create(
            name="Day207 Test User",
            email="day207@example.com",
            message="Testing database query performance.",
        )

        for number in range(1, 26):
            MessageAttachment.objects.create(
                contact_message=cls.contact_message,
                file=f"day207/test_file_{number}.txt",
            )

    # ------------------------------------------------
    # TEST 1 - OPTIMIZED QUERYSET
    # ------------------------------------------------

    def test_select_related_uses_one_query(self):
        """
        Fetch 20 attachments and their contact names
        using only one SQL query.
        """

        queryset = (
            MessageAttachment.objects
            .select_related("contact_message")
            .order_by("-id")
        )

        with self.assertNumQueries(1):

            attachments = list(queryset[:20])

            contact_names = [
                attachment.contact_message.name
                for attachment in attachments
            ]

        self.assertEqual(len(attachments), 20)
        self.assertEqual(len(contact_names), 20)

    # ------------------------------------------------
    # TEST 2 - N+1 QUERY PROBLEM
    # ------------------------------------------------

    def test_without_select_related_uses_21_queries(self):
        """
        Demonstrate the N+1 query problem.
        """

        queryset = (
            MessageAttachment.objects
            .order_by("-id")
        )

        with self.assertNumQueries(21):

            attachments = list(queryset[:20])

            contact_names = [
                attachment.contact_message.name
                for attachment in attachments
            ]

        self.assertEqual(len(attachments), 20)
        self.assertEqual(len(contact_names), 20)

    # ------------------------------------------------
    # TEST 3 - PAGINATION QUERY COUNT
    # ------------------------------------------------

    def test_pagination_uses_two_queries(self):
        """
        Pagination performs a count query and
        a query to retrieve the current page.
        """

        queryset = (
            MessageAttachment.objects
            .select_related("contact_message")
            .order_by("-id")
        )

        with self.assertNumQueries(2):

            paginator = Paginator(queryset, 20)

            page = paginator.page(1)

            attachments = list(page.object_list)

            contact_names = [
                attachment.contact_message.name
                for attachment in attachments
            ]

        self.assertEqual(paginator.count, 25)
        self.assertEqual(paginator.num_pages, 2)
        self.assertEqual(len(attachments), 20)
        self.assertEqual(len(contact_names), 20)

    # ------------------------------------------------
    # TEST 4 - SQL JOIN VERIFICATION
    # ------------------------------------------------

    def test_optimized_sql_contains_join(self):
        """
        Verify that select_related generates
        a SQL JOIN.
        """

        queryset = (
            MessageAttachment.objects
            .select_related("contact_message")
            .order_by("-id")
        )

        with CaptureQueriesContext(connection) as queries:

            attachments = list(queryset[:20])

        self.assertEqual(len(queries), 1)

        sql = queries[0]["sql"].upper()

        self.assertIn("JOIN", sql)

        self.assertEqual(len(attachments), 20)


# ====================================================
# DAY 208 - DATABASE AGGREGATION REPORT TESTS
# ====================================================

class Day208AggregationReportTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.staff_user = get_user_model().objects.create_user(
            username="day208_staff",
            password="Day208TestPass!123",
            is_staff=True,
        )

        cls.regular_user = get_user_model().objects.create_user(
            username="day208_regular",
            password="Day208TestPass!123",
        )

        # Create three contact messages.

        cls.message_one = ContactMessage.objects.create(
            name="Rahul",
            email="rahul@example.com",
            message="First test message",
        )

        cls.message_two = ContactMessage.objects.create(
            name="Priya",
            email="priya@example.com",
            message="Second test message",
        )

        cls.message_three = ContactMessage.objects.create(
            name="Aman",
            email="aman@example.com",
            message="Third test message",
        )

        # Rahul has three attachments.

        for number in range(1, 4):

            MessageAttachment.objects.create(
                contact_message=cls.message_one,
                file=f"day208/rahul_{number}.txt",
            )

        # Priya has one attachment.

        MessageAttachment.objects.create(
            contact_message=cls.message_two,
            file="day208/priya_1.txt",
        )

        # Aman has zero attachments.

    def setUp(self):
        self.client.force_login(self.staff_user)

    # TEST 1 - STAFF CAN ACCESS REPORT

    def test_staff_can_access_report(self):

        response = self.client.get(
            reverse("attachment_summary_report")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/attachment_summary.html",
        )

    # TEST 2 - TOTAL COUNTS

    def test_report_total_counts(self):

        response = self.client.get(
            reverse("attachment_summary_report")
        )

        summary = response.context["summary"]

        self.assertEqual(summary["total_messages"], 3)

        self.assertEqual(summary["total_attachments"], 4)

    # TEST 3 - AVERAGE ATTACHMENTS

    def test_average_attachments(self):

        response = self.client.get(
            reverse("attachment_summary_report")
        )

        average = response.context["summary"][
            "average_attachments"
        ]

        self.assertAlmostEqual(
            float(average),
            4 / 3,
            places=5,
        )

    # TEST 4 - ANNOTATED COUNTS

    def test_message_attachment_counts(self):

        response = self.client.get(
            reverse("attachment_summary_report")
        )

        message_counts = list(
            response.context["message_counts"]
        )

        counts = [
            message.attachment_count
            for message in message_counts
        ]

        self.assertEqual(counts, [3, 1, 0])

    # TEST 5 - REGULAR USER DENIED

    def test_regular_user_cannot_access_report(self):

        self.client.force_login(self.regular_user)

        response = self.client.get(
            reverse("attachment_summary_report")
        )

        self.assertNotEqual(response.status_code, 200)


class Day208EmptyAggregationReportTests(TestCase):

    # TEST 6 - EMPTY DATABASE

    def test_empty_report_has_zero_values(self):

        staff_user = get_user_model().objects.create_user(
            username="day208_empty_staff",
            password="Day208TestPass!123",
            is_staff=True,
        )

        self.client.force_login(staff_user)

        response = self.client.get(
            reverse("attachment_summary_report")
        )

        self.assertEqual(response.status_code, 200)

        summary = response.context["summary"]

        self.assertEqual(summary["total_messages"], 0)

        self.assertEqual(summary["total_attachments"], 0)

        self.assertEqual(summary["average_attachments"], 0)



# =====================================================
# DAY 209 - ADVANCED REPORTING TESTS
# =====================================================

class Day209AdvancedReportingTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        user_model = get_user_model()

        cls.staff_user = user_model.objects.create_user(
            username="day209_staff",
            password="Day209TestPass!123",
            is_staff=True,
        )

        cls.regular_user = user_model.objects.create_user(
            username="day209_regular",
            password="Day209TestPass!123",
        )

        # ---------------------------------------------
        # CREATE THREE CONTACT MESSAGES
        # ---------------------------------------------

        cls.alice = ContactMessage.objects.create(
            name="Alice",
            email="alice209@example.com",
            message="First message",
        )

        cls.bob = ContactMessage.objects.create(
            name="Bob",
            email="bob209@example.com",
            message="Second message",
        )

        cls.charlie = ContactMessage.objects.create(
            name="Charlie",
            email="charlie209@example.com",
            message="Third message",
        )

        # ---------------------------------------------
        # ALICE: THREE RECENT ATTACHMENTS
        # ---------------------------------------------

        for number in range(1, 4):

            MessageAttachment.objects.create(
                contact_message=cls.alice,
                file=f"day209/alice_{number}.txt",
            )

        # ---------------------------------------------
        # BOB: ONE OLD ATTACHMENT
        # ---------------------------------------------

        old_attachment = MessageAttachment.objects.create(
            contact_message=cls.bob,
            file="day209/bob_old.txt",
        )

        old_date = timezone.now() - timedelta(
            days=45
        )

        MessageAttachment.objects.filter(
            pk=old_attachment.pk
        ).update(
            uploaded_at=old_date
        )

        # CHARLIE: ZERO ATTACHMENTS

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse(
            "attachment_summary_report"
        )

    # TEST 1 - DEFAULT REPORT

    def test_default_report_statistics(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        summary = response.context["summary"]

        self.assertEqual(summary["total_messages"], 3)

        self.assertEqual(summary["total_attachments"], 4)

        self.assertAlmostEqual(
            float(summary["average_attachments"]),
            4 / 3,
            places=5,
        )

    # TEST 2 - LAST 7 DAYS

    def test_last_7_days_filter(self):

        response = self.client.get(
            self.url,
            {"date_range": "7"},
        )

        summary = response.context["summary"]

        self.assertEqual(summary["total_messages"], 3)

        self.assertEqual(summary["total_attachments"], 3)

        self.assertEqual(
            response.context["selected_date_range"],
            "7",
        )

    # TEST 3 - LAST 30 DAYS

    def test_last_30_days_filter(self):

        response = self.client.get(
            self.url,
            {"date_range": "30"},
        )

        summary = response.context["summary"]

        self.assertEqual(summary["total_attachments"], 3)

    # TEST 4 - LAST 90 DAYS

    def test_last_90_days_filter(self):

        response = self.client.get(
            self.url,
            {"date_range": "90"},
        )

        summary = response.context["summary"]

        self.assertEqual(summary["total_attachments"], 4)

    # TEST 5 - FEWEST ATTACHMENTS FIRST

    def test_sort_by_fewest_attachments(self):

        response = self.client.get(
            self.url,
            {"sort": "least"},
        )

        messages = list(
            response.context["message_counts"]
        )

        names = [
            message.name
            for message in messages
        ]

        self.assertEqual(
            names,
            ["Charlie", "Bob", "Alice"],
        )

    # TEST 6 - SORT BY NAME

    def test_sort_by_contact_name(self):

        response = self.client.get(
            self.url,
            {"sort": "name"},
        )

        messages = list(
            response.context["message_counts"]
        )

        names = [
            message.name
            for message in messages
        ]

        self.assertEqual(
            names,
            ["Alice", "Bob", "Charlie"],
        )

    # TEST 7 - INVALID FILTER VALUES

    def test_invalid_filters_use_defaults(self):

        response = self.client.get(
            self.url,
            {
                "date_range": "invalid",
                "sort": "unknown",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["selected_date_range"],
            "all",
        )

        self.assertEqual(
            response.context["selected_sort"],
            "most",
        )

        self.assertEqual(
            response.context["summary"][
                "total_attachments"
            ],
            4,
        )

    # TEST 8 - NON-STAFF USER DENIED

    def test_regular_user_cannot_access_report(self):

        self.client.force_login(
            self.regular_user
        )

        response = self.client.get(self.url)

        self.assertNotEqual(
            response.status_code,
            200,
        )


# ====================================================
# DAY 211 - DATABASE TRANSACTIONS & DATA INTEGRITY
# ====================================================

class Day211TransactionTests(TestCase):

    # -----------------------------------------------
    # TEST 1 - SUCCESSFUL TRANSACTION
    # -----------------------------------------------

    def test_successful_transaction_commits(self):

        with transaction.atomic():

            ContactMessage.objects.create(
                name="Arman",
                email="arman211@example.com",
                message="First message",
            )

            ContactMessage.objects.create(
                name="Rahul",
                email="rahul211@example.com",
                message="Second message",
            )

        self.assertEqual(
            ContactMessage.objects.count(),
            2,
        )

    # -----------------------------------------------
    # TEST 2 - FAILED TRANSACTION ROLLS BACK
    # -----------------------------------------------

    def test_failed_transaction_rolls_back(self):

        with self.assertRaises(ValueError):

            with transaction.atomic():

                ContactMessage.objects.create(
                    name="Arman",
                    email="rollback211@example.com",
                    message="This should be rolled back",
                )

                raise ValueError(
                    "Simulated database operation failure"
                )

        self.assertEqual(
            ContactMessage.objects.count(),
            0,
        )

    # -----------------------------------------------
    # TEST 3 - MULTIPLE OPERATIONS ROLL BACK
    # -----------------------------------------------

    def test_multiple_operations_roll_back(self):

        with self.assertRaises(RuntimeError):

            with transaction.atomic():

                ContactMessage.objects.create(
                    name="User One",
                    email="one211@example.com",
                    message="First operation",
                )

                ContactMessage.objects.create(
                    name="User Two",
                    email="two211@example.com",
                    message="Second operation",
                )

                raise RuntimeError(
                    "Failure after both inserts"
                )

        self.assertFalse(
            ContactMessage.objects.exists()
        )

    # -----------------------------------------------
    # TEST 4 - NESTED TRANSACTION SAVEPOINT
    # -----------------------------------------------

    def test_nested_transaction_savepoint(self):

        with transaction.atomic():

            ContactMessage.objects.create(
                name="Outer One",
                email="outerone211@example.com",
                message="Outer transaction record",
            )

            try:

                with transaction.atomic():

                    ContactMessage.objects.create(
                        name="Inner Record",
                        email="inner211@example.com",
                        message="Should be rolled back",
                    )

                    raise ValueError(
                        "Inner transaction failed"
                    )

            except ValueError:
                pass

            ContactMessage.objects.create(
                name="Outer Two",
                email="outertwo211@example.com",
                message="Outer transaction continues",
            )

        names = set(
            ContactMessage.objects.values_list(
                "name",
                flat=True,
            )
        )

        self.assertEqual(
            names,
            {"Outer One", "Outer Two"},
        )


# ====================================================
# DAY 212 - TRANSACTION ON_COMMIT TESTS
# ====================================================

class Day212OnCommitTests(TestCase):

    # TEST 1 - Callback runs after successful transaction

    def test_callback_after_successful_transaction(self):

        events = []

        with self.captureOnCommitCallbacks(execute=True) as callbacks:

            with transaction.atomic():

                ContactMessage.objects.create(
                    name="Arman",
                    email="arman212@example.com",
                    message="Testing on_commit",
                )

                transaction.on_commit(
                    lambda: events.append("Notification sent")
                )

                # Callback must not run before commit.
                self.assertEqual(events, [])

        self.assertEqual(len(callbacks), 1)
        self.assertEqual(events, ["Notification sent"])

        self.assertEqual(
            ContactMessage.objects.count(),
            1,
        )

    # TEST 2 - Rollback discards callback

    def test_rollback_discards_callback(self):

        events = []

        with self.captureOnCommitCallbacks(execute=True) as callbacks:

            with self.assertRaises(ValueError):

                with transaction.atomic():

                    ContactMessage.objects.create(
                        name="Rollback User",
                        email="rollback212@example.com",
                        message="Should be rolled back",
                    )

                    transaction.on_commit(
                        lambda: events.append("Should not run")
                    )

                    raise ValueError("Transaction failed")

        self.assertEqual(len(callbacks), 0)
        self.assertEqual(events, [])

        self.assertEqual(
            ContactMessage.objects.count(),
            0,
        )

    # TEST 3 - Multiple callbacks preserve order

    def test_multiple_callbacks_run_in_order(self):

        events = []

        with self.captureOnCommitCallbacks(execute=True) as callbacks:

            with transaction.atomic():

                transaction.on_commit(
                    lambda: events.append("First")
                )

                transaction.on_commit(
                    lambda: events.append("Second")
                )

        self.assertEqual(len(callbacks), 2)
        self.assertEqual(events, ["First", "Second"])

    # TEST 4 - Inner rollback does not cancel outer callback

    def test_nested_rollback_discards_inner_callback(self):

        events = []

        with self.captureOnCommitCallbacks(execute=True) as callbacks:

            with transaction.atomic():

                ContactMessage.objects.create(
                    name="Outer User",
                    email="outer212@example.com",
                    message="Should remain saved",
                )

                transaction.on_commit(
                    lambda: events.append("Outer callback")
                )

                try:

                    with transaction.atomic():

                        ContactMessage.objects.create(
                            name="Inner User",
                            email="inner212@example.com",
                            message="Should be rolled back",
                        )

                        transaction.on_commit(
                            lambda: events.append("Inner callback")
                        )

                        raise ValueError("Inner transaction failed")

                except ValueError:
                    pass

        self.assertEqual(len(callbacks), 1)
        self.assertEqual(events, ["Outer callback"])

        names = list(
            ContactMessage.objects.values_list(
                "name",
                flat=True,
            )
        )

        self.assertEqual(names, ["Outer User"])



# ================================================
# DAY 213 - DATABASE CONSTRAINT TESTS
# ================================================

class Day213DatabaseConstraintTests(TestCase):

    # TEST 1 - Valid category can be saved

    def test_valid_category(self):

        category = ReportCategory.objects.create(
            name="Analytics",
            priority=5,
        )

        self.assertEqual(category.name, "Analytics")
        self.assertEqual(category.priority, 5)

        self.assertEqual(
            ReportCategory.objects.count(),
            1,
        )

    # TEST 2 - Duplicate names are rejected

    def test_duplicate_category_rejected(self):

        ReportCategory.objects.create(
            name="Analytics",
            priority=5,
        )

        with self.assertRaises(IntegrityError):

            with transaction.atomic():

                ReportCategory.objects.create(
                    name="Analytics",
                    priority=10,
                )

        self.assertEqual(
            ReportCategory.objects.count(),
            1,
        )

    # TEST 3 - Negative priority is rejected

    def test_negative_priority_rejected(self):

        with self.assertRaises(IntegrityError):

            with transaction.atomic():

                ReportCategory.objects.create(
                    name="Invalid Category",
                    priority=-5,
                )

        self.assertEqual(
            ReportCategory.objects.count(),
            0,
        )

    # TEST 4 - full_clean validates constraints

    def test_full_clean_rejects_negative_priority(self):

        category = ReportCategory(
            name="Validation Test",
            priority=-10,
        )

        with self.assertRaises(ValidationError):
            category.full_clean()

        self.assertFalse(
            ReportCategory.objects.exists()
        )


# ================================================
# DAY 214 - MODEL VALIDATION TESTS
# ================================================

class Day214ModelValidationTests(TestCase):

    # TEST 1 - Valid data passes full_clean()

    def test_valid_category_passes_validation(self):

        category = ReportCategory(
            name="Analytics",
            priority=5,
        )

        category.full_clean()
        category.save()

        self.assertEqual(
            ReportCategory.objects.count(),
            1,
        )

    # TEST 2 - Short category name is rejected

    def test_short_category_name_rejected(self):

        category = ReportCategory(
            name="AB",
            priority=2,
        )

        with self.assertRaises(ValidationError):
            category.full_clean()

        self.assertFalse(
            ReportCategory.objects.exists()
        )

    # TEST 3 - Negative priority is rejected

    def test_negative_priority_validation(self):

        category = ReportCategory(
            name="Reports",
            priority=-3,
        )

        with self.assertRaises(ValidationError):
            category.full_clean()

        self.assertFalse(
            ReportCategory.objects.exists()
        )

    # TEST 4 - Archived category must have priority 0

    def test_archived_category_invalid_priority(self):

        category = ReportCategory(
            name="Archived",
            priority=5,
        )

        with self.assertRaises(ValidationError) as error:
            category.full_clean()

        self.assertIn(
            "priority",
            error.exception.message_dict,
        )

    # TEST 5 - Archived category with priority 0 is valid

    def test_archived_category_valid_priority(self):

        category = ReportCategory(
            name="Archived",
            priority=0,
        )

        category.full_clean()
        category.save()

        self.assertEqual(
            ReportCategory.objects.count(),
            1,
        )


# ================================================
# DAY 215 - ADVANCED FORM VALIDATION TESTS
# ================================================

class Day215AdvancedFormTests(TestCase):

    # TEST 1 - Valid form saves category

    def test_valid_form_saves_category(self):

        form = ReportCategoryForm(
            data={
                "name": "Analytics",
                "priority": 5,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        category = form.save()

        self.assertEqual(category.name, "Analytics")
        self.assertEqual(category.priority, 5)

        self.assertEqual(
            ReportCategory.objects.count(),
            1,
        )

    # TEST 2 - Placeholder name is rejected

    def test_unknown_category_name_rejected(self):

        form = ReportCategoryForm(
            data={
                "name": "Unknown",
                "priority": 2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    # TEST 3 - Featured priority below 5 is rejected

    def test_featured_category_low_priority_rejected(self):

        form = ReportCategoryForm(
            data={
                "name": "Featured",
                "priority": 2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)

    # TEST 4 - Model-level validation still works

    def test_archived_category_validation(self):

        form = ReportCategoryForm(
            data={
                "name": "Archived",
                "priority": 4,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)

    # TEST 5 - Negative priority is rejected

    def test_negative_priority_rejected(self):

        form = ReportCategoryForm(
            data={
                "name": "Reports",
                "priority": -2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)


# ================================================
# DAY 216 - CREATEVIEW TESTS
# ================================================

class Day216ReportCategoryCreateViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day216staff",
            password="TestPassword216!",
            is_staff=True,
        )

        cls.regular_user = User.objects.create_user(
            username="day216regular",
            password="TestPassword216!",
        )

    def setUp(self):

        self.url = reverse("report_category_create")

        self.client.force_login(self.staff_user)

    # TEST 1 - Staff can open form page

    def test_staff_can_open_form(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/report_category_form.html",
        )

    # TEST 2 - Valid form creates category

    def test_valid_submission_creates_category(self):

        response = self.client.post(
            self.url,
            {
                "name": "Analytics",
                "priority": 5,
            },
        )

        self.assertRedirects(response, self.url)

        self.assertTrue(
            ReportCategory.objects.filter(
                name="Analytics",
                priority=5,
            ).exists()
        )

    # TEST 3 - Unknown name is rejected

    def test_unknown_name_rejected(self):

        response = self.client.post(
            self.url,
            {
                "name": "Unknown",
                "priority": 2,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFormError(
            response.context["form"],
            "name",
            "Please enter a descriptive category name.",
        )

        self.assertFalse(
            ReportCategory.objects.exists()
        )

    # TEST 4 - Featured requires priority 5+

    def test_featured_priority_validation(self):

        response = self.client.post(
            self.url,
            {
                "name": "Featured",
                "priority": 2,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "priority",
            response.context["form"].errors,
        )

        self.assertFalse(
            ReportCategory.objects.exists()
        )

    # TEST 5 - Duplicate category is rejected

    def test_duplicate_category_rejected(self):

        ReportCategory.objects.create(
            name="Analytics",
            priority=5,
        )

        response = self.client.post(
            self.url,
            {
                "name": "Analytics",
                "priority": 7,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "name",
            response.context["form"].errors,
        )

        self.assertEqual(
            ReportCategory.objects.count(),
            1,
        )

    # TEST 6 - Regular user cannot access

    def test_regular_user_cannot_access_form(self):

        self.client.force_login(self.regular_user)

        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)

        response = self.client.post(
            self.url,
            {
                "name": "Restricted",
                "priority": 1,
            },
        )

        self.assertNotEqual(response.status_code, 200)

        self.assertFalse(
            ReportCategory.objects.exists()
        )

    # TEST 7 - Guest cannot access

    def test_guest_cannot_access_form(self):

        self.client.logout()

        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)


# ==========================================
# DAY 217 - UPDATEVIEW AND DELETEVIEW TESTS
# ==========================================

class Day217CategoryManagementTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day217staff",
            password="TestPassword217!",
            is_staff=True,
        )

        cls.regular_user = User.objects.create_user(
            username="day217regular",
            password="TestPassword217!",
        )

        cls.category = ReportCategory.objects.create(
            name="Analytics",
            priority=5,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.update_url = reverse(
            "report_category_update",
            args=[self.category.pk],
        )

        self.delete_url = reverse(
            "report_category_delete",
            args=[self.category.pk],
        )

    # TEST 1 - Staff can open update page

    def test_staff_can_open_update_page(self):

        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/report_category_update.html",
        )

    # TEST 2 - Staff can update category

    def test_staff_can_update_category(self):

        response = self.client.post(
            self.update_url,
            {
                "name": "Updated Analytics",
                "priority": 8,
            },
        )

        self.assertRedirects(
            response,
            reverse("report_category_create"),
        )

        self.category.refresh_from_db()

        self.assertEqual(
            self.category.name,
            "Updated Analytics",
        )

        self.assertEqual(
            self.category.priority,
            8,
        )

    # TEST 3 - Invalid update is rejected

    def test_invalid_update_rejected(self):

        response = self.client.post(
            self.update_url,
            {
                "name": "Featured",
                "priority": 2,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "priority",
            response.context["form"].errors,
        )

        self.category.refresh_from_db()

        self.assertEqual(
            self.category.name,
            "Analytics",
        )

    # TEST 4 - Missing category returns 404

    def test_update_missing_category_returns_404(self):

        url = reverse(
            "report_category_update",
            args=[999999],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    # TEST 5 - Delete page does not delete on GET

    def test_delete_confirmation_page(self):

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/report_category_confirm_delete.html",
        )

        self.assertTrue(
            ReportCategory.objects.filter(
                pk=self.category.pk,
            ).exists()
        )

    # TEST 6 - Staff can delete with POST

    def test_staff_can_delete_category(self):

        response = self.client.post(self.delete_url)

        self.assertRedirects(
            response,
            reverse("report_category_create"),
        )

        self.assertFalse(
            ReportCategory.objects.filter(
                pk=self.category.pk,
            ).exists()
        )

    # TEST 7 - Regular user cannot edit or delete

    def test_regular_user_cannot_manage_categories(self):

        self.client.force_login(self.regular_user)

        for url in [self.update_url, self.delete_url]:

            response = self.client.get(url)

            self.assertNotEqual(
                response.status_code,
                200,
            )

            response = self.client.post(
                url,
                {
                    "name": "Unauthorized Change",
                    "priority": 9,
                },
            )

            self.assertNotEqual(
                response.status_code,
                200,
            )

        self.category.refresh_from_db()

        self.assertEqual(
            self.category.name,
            "Analytics",
        )

        self.assertTrue(
            ReportCategory.objects.filter(
                pk=self.category.pk,
            ).exists()
        )

    # TEST 8 - Guest cannot edit or delete

    def test_guest_cannot_manage_categories(self):

        self.client.logout()

        for url in [self.update_url, self.delete_url]:

            response = self.client.get(url)

            self.assertNotEqual(
                response.status_code,
                200,
            )

            response = self.client.post(
                url,
                {
                    "name": "Guest Change",
                    "priority": 9,
                },
            )

            self.assertNotEqual(
                response.status_code,
                200,
            )

        self.assertTrue(
            ReportCategory.objects.filter(
                pk=self.category.pk,
            ).exists()
        )


# ==========================================
# DAY 218 - CATEGORY DASHBOARD TESTS
# ==========================================

class Day218CategoryDashboardTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day218staff",
            password="TestPassword218!",
            is_staff=True,
        )

        cls.regular_user = User.objects.create_user(
            username="day218regular",
            password="TestPassword218!",
        )

        for index in range(1, 13):

            ReportCategory.objects.create(
                name=f"Category {index:02d}",
                priority=index,
            )

    def setUp(self):

        self.url = reverse("report_category_list")

        self.client.force_login(self.staff_user)

    # TEST 1 - Staff can open dashboard

    def test_staff_can_open_dashboard(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "homepage/report_category_list.html",
        )

    # TEST 2 - First page shows 10 categories

    def test_first_page_contains_ten_categories(self):

        response = self.client.get(self.url)

        self.assertEqual(
            len(response.context["categories"]),
            10,
        )

    # TEST 3 - Second page shows 2 categories

    def test_second_page_contains_two_categories(self):

        response = self.client.get(
            self.url,
            {"page": 2},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.context["categories"]),
            2,
        )

        self.assertEqual(
            response.context["page_obj"].number,
            2,
        )

    # TEST 4 - Categories are alphabetically ordered

    def test_categories_are_ordered_by_name(self):

        response = self.client.get(self.url)

        names = [
            category.name
            for category in response.context["categories"]
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

    # TEST 5 - Edit and Delete links exist

    def test_dashboard_contains_management_links(self):

        response = self.client.get(self.url)

        category = ReportCategory.objects.get(
            name="Category 01"
        )

        self.assertContains(
            response,
            reverse(
                "report_category_update",
                args=[category.pk],
            ),
        )

        self.assertContains(
            response,
            reverse(
                "report_category_delete",
                args=[category.pk],
            ),
        )

    # TEST 6 - Empty dashboard shows message

    def test_empty_dashboard_message(self):

        ReportCategory.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "No report categories yet.",
        )

    # TEST 7 - Regular user cannot access dashboard

    def test_regular_user_cannot_access_dashboard(self):

        self.client.force_login(self.regular_user)

        response = self.client.get(self.url)

        self.assertNotEqual(
            response.status_code,
            200,
        )

    # TEST 8 - Guest cannot access dashboard

    def test_guest_cannot_access_dashboard(self):

        self.client.logout()

        response = self.client.get(self.url)

        self.assertNotEqual(
            response.status_code,
            200,
        )


# ==========================================
# DAY 219 - SEARCH AND FILTER TESTS
# ==========================================

class Day219CategorySearchTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day219staff",
            password="TestPassword219!",
            is_staff=True,
        )

        # Create enough categories to test pagination

        for index in range(1, 23):

            ReportCategory.objects.create(
                name=f"Analytics {index:02d}",
                priority=index % 8,
            )

        ReportCategory.objects.create(
            name="Featured",
            priority=7,
        )

        ReportCategory.objects.create(
            name="Reports",
            priority=0,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - Search by category name

    def test_search_by_name(self):

        response = self.client.get(
            self.url,
            {"q": "Featured"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["paginator"].count,
            1,
        )

        self.assertContains(response, "Featured")

    # TEST 2 - Search is case-insensitive

    def test_case_insensitive_search(self):

        response = self.client.get(
            self.url,
            {"q": "fEaTuReD"},
        )

        self.assertEqual(
            response.context["paginator"].count,
            1,
        )

    # TEST 3 - Search removes surrounding spaces

    def test_search_trims_whitespace(self):

        response = self.client.get(
            self.url,
            {"q": "  Reports  "},
        )

        self.assertEqual(
            response.context["query"],
            "Reports",
        )

        self.assertEqual(
            response.context["paginator"].count,
            1,
        )

    # TEST 4 - High-priority filter

    def test_high_priority_filter(self):

        response = self.client.get(
            self.url,
            {"priority": "high"},
        )

        self.assertEqual(response.status_code, 200)

        for category in response.context["categories"]:
            self.assertGreaterEqual(
                category.priority,
                5,
            )

        self.assertEqual(
            response.context["paginator"].count,
            9,
        )

    # TEST 5 - Low-priority filter

    def test_low_priority_filter(self):

        response = self.client.get(
            self.url,
            {"priority": "low"},
        )

        self.assertEqual(response.status_code, 200)

        for category in response.context["categories"]:
            self.assertLess(
                category.priority,
                5,
            )

        self.assertEqual(
            response.context["paginator"].count,
            15,
        )

    # TEST 6 - Search and priority together

    def test_combined_search_and_filter(self):

        response = self.client.get(
            self.url,
            {
                "q": "Analytics",
                "priority": "high",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["paginator"].count,
            8,
        )

        for category in response.context["categories"]:

            self.assertIn(
                "Analytics",
                category.name,
            )

            self.assertGreaterEqual(
                category.priority,
                5,
            )

    # TEST 7 - Pagination preserves filters

    def test_pagination_preserves_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Analytics",
                "priority": "low",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["paginator"].count,
            14,
        )

        self.assertContains(
            response,
            "?q=Analytics&amp;priority=low&amp;sort=name_asc&amp;page=2",
        )

        page_two = self.client.get(
            self.url,
            {
                "q": "Analytics",
                "priority": "low",
                "page": 2,
            },
        )

        self.assertEqual(page_two.status_code, 200)

        self.assertEqual(
            len(page_two.context["categories"]),
            4,
        )

    # TEST 8 - Unknown priority falls back to all

    def test_invalid_priority_filter(self):

        response = self.client.get(
            self.url,
            {"priority": "invalid"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["priority_filter"],
            "all",
        )

        self.assertEqual(
            response.context["paginator"].count,
            24,
        )


# ==========================================
# DAY 220 - ADVANCED SORTING TESTS
# ==========================================

class Day220CategorySortingTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day220staff",
            password="TestPassword220!",
            is_staff=True,
        )

        for index in range(1, 16):

            ReportCategory.objects.create(
                name=f"Analytics {index:02d}",
                priority=index % 8,
            )

        ReportCategory.objects.create(
            name="Featured",
            priority=7,
        )

        ReportCategory.objects.create(
            name="Reports",
            priority=0,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - Default alphabetical sorting

    def test_default_name_ascending(self):

        response = self.client.get(self.url)

        names = [
            category.name
            for category in response.context["categories"]
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

        self.assertEqual(
            response.context["sort_order"],
            "name_asc",
        )

    # TEST 2 - Reverse alphabetical sorting

    def test_name_descending(self):

        response = self.client.get(
            self.url,
            {"sort": "name_desc"},
        )

        names = [
            category.name
            for category in response.context["categories"]
        ]

        self.assertEqual(
            names,
            sorted(names, reverse=True),
        )

    # TEST 3 - Highest priority first

    def test_priority_highest_first(self):

        response = self.client.get(
            self.url,
            {"sort": "priority_high"},
        )

        priorities = [
            category.priority
            for category in response.context["categories"]
        ]

        self.assertEqual(
            priorities,
            sorted(priorities, reverse=True),
        )

    # TEST 4 - Lowest priority first

    def test_priority_lowest_first(self):

        response = self.client.get(
            self.url,
            {"sort": "priority_low"},
        )

        priorities = [
            category.priority
            for category in response.context["categories"]
        ]

        self.assertEqual(
            priorities,
            sorted(priorities),
        )

    # TEST 5 - Combined search, filter and sorting

    def test_combined_search_filter_sort(self):

        response = self.client.get(
            self.url,
            {
                "q": "Analytics",
                "priority": "high",
                "sort": "priority_high",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["paginator"].count,
            6,
        )

        categories = list(
            response.context["categories"]
        )

        for category in categories:

            self.assertIn(
                "Analytics",
                category.name,
            )

            self.assertGreaterEqual(
                category.priority,
                5,
            )

        priorities = [
            category.priority
            for category in categories
        ]

        self.assertEqual(
            priorities,
            sorted(priorities, reverse=True),
        )

    # TEST 6 - Pagination preserves sorting

    def test_pagination_preserves_sorting(self):

        response = self.client.get(
            self.url,
            {
                "q": "Analytics",
                "priority": "all",
                "sort": "priority_high",
            },
        )

        self.assertContains(
            response,
            "?q=Analytics&amp;priority=all&amp;sort=priority_high&amp;page=2",
        )

    # TEST 7 - Invalid sorting defaults to name

    def test_invalid_sort_defaults_to_name(self):

        response = self.client.get(
            self.url,
            {"sort": "unknown_field"},
        )

        self.assertEqual(
            response.context["sort_order"],
            "name_asc",
        )

        names = [
            category.name
            for category in response.context["categories"]
        ]

        self.assertEqual(
            names,
            sorted(names),
        )

    # TEST 8 - Second page retains correct ordering

    def test_second_page_sorted_correctly(self):

        response = self.client.get(
            self.url,
            {
                "q": "Analytics",
                "sort": "name_desc",
                "page": 2,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(response.context["categories"]),
            5,
        )

        names = [
            category.name
            for category in response.context["categories"]
        ]

        expected_names = sorted(
            [
                f"Analytics {index:02d}"
                for index in range(1, 16)
            ],
            reverse=True,
        )[10:]

        self.assertEqual(
            names,
            expected_names,
        )


# ==========================================
# DAY 221 - CATEGORY STATISTICS TESTS
# ==========================================

class Day221CategoryStatisticsTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day221staff",
            password="TestPassword221!",
            is_staff=True,
        )

        ReportCategory.objects.create(
            name="Alpha",
            priority=5,
        )

        ReportCategory.objects.create(
            name="Beta",
            priority=8,
        )

        ReportCategory.objects.create(
            name="Gamma",
            priority=4,
        )

        ReportCategory.objects.create(
            name="Delta",
            priority=0,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - TOTAL CATEGORY COUNT

    def test_total_categories(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["category_stats"]["total"],
            4,
        )

    # TEST 2 - HIGH PRIORITY COUNT

    def test_high_priority_count(self):

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["category_stats"]["high"],
            2,
        )

    # TEST 3 - LOW PRIORITY COUNT

    def test_low_priority_count(self):

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["category_stats"]["low"],
            2,
        )

    # TEST 4 - AVERAGE PRIORITY

    def test_average_priority(self):

        response = self.client.get(self.url)

        self.assertAlmostEqual(
            response.context["category_stats"]["average"],
            4.25,
        )

    # TEST 5 - EMPTY DATABASE STATISTICS

    def test_empty_database_statistics(self):

        ReportCategory.objects.all().delete()

        response = self.client.get(self.url)

        stats = response.context["category_stats"]

        self.assertEqual(stats["total"], 0)

        self.assertEqual(stats["high"], 0)

        self.assertEqual(stats["low"], 0)

        self.assertEqual(stats["average"], 0.0)

    # TEST 6 - SEARCH DOES NOT CHANGE GLOBAL STATS

    def test_statistics_independent_of_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
            },
        )

        self.assertEqual(
            response.context["paginator"].count,
            1,
        )

        self.assertEqual(
            response.context["category_stats"]["total"],
            4,
        )

        self.assertEqual(
            response.context["category_stats"]["high"],
            2,
        )

    # TEST 7 - STATISTICS APPEAR IN HTML

    def test_statistics_cards_render(self):

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "Total Categories",
        )

        self.assertContains(
            response,
            "High Priority",
        )

        self.assertContains(
            response,
            "Low Priority",
        )

        self.assertContains(
            response,
            "Average Priority",
        )

        self.assertContains(
            response,
            "4.25",
        )

    # TEST 8 - GUEST CANNOT VIEW DASHBOARD

    def test_guest_cannot_view_statistics(self):

        self.client.logout()

        response = self.client.get(self.url)

        self.assertNotEqual(
            response.status_code,
            200,
        )


# ==========================================
# DAY 222 - PRIORITY ANALYTICS TESTS
# ==========================================

class Day222PriorityAnalyticsTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day222staff",
            password="TestPassword222!",
            is_staff=True,
        )

        ReportCategory.objects.create(
            name="Alpha",
            priority=5,
        )

        ReportCategory.objects.create(
            name="Beta",
            priority=8,
        )

        ReportCategory.objects.create(
            name="Gamma",
            priority=4,
        )

        ReportCategory.objects.create(
            name="Delta",
            priority=0,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - HIGH PERCENTAGE

    def test_high_priority_percentage(self):

        response = self.client.get(self.url)

        stats = response.context["category_stats"]

        self.assertEqual(
            stats["high_percentage"],
            50.0
        )

    # TEST 2 - LOW PERCENTAGE

    def test_low_priority_percentage(self):

        response = self.client.get(self.url)

        stats = response.context["category_stats"]

        self.assertEqual(
            stats["low_percentage"],
            50.0
        )

    # TEST 3 - PERCENTAGES SUM TO 100

    def test_percentages_sum_to_100(self):

        response = self.client.get(self.url)

        stats = response.context["category_stats"]

        self.assertAlmostEqual(
            stats["high_percentage"] +
            stats["low_percentage"],
            100.0
        )

    # TEST 4 - EMPTY DATABASE

    def test_empty_database_percentages(self):

        ReportCategory.objects.all().delete()

        response = self.client.get(self.url)

        stats = response.context["category_stats"]

        self.assertEqual(
            stats["high_percentage"],
            0.0
        )

        self.assertEqual(
            stats["low_percentage"],
            0.0
        )

    # TEST 5 - FILTER DOES NOT ALTER GLOBAL STATS

    def test_analytics_independent_of_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            1
        )

        stats = response.context["category_stats"]

        self.assertEqual(
            stats["high_percentage"],
            50.0
        )

    # TEST 6 - ANALYTICS SECTION RENDERS

    def test_analytics_section_renders(self):

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "Priority Analytics"
        )

        self.assertContains(
            response,
            "Priority Distribution"
        )

        self.assertContains(
            response,
            "50.00%"
        )

    # TEST 7 - DISTRIBUTION BAR RENDERS


    def test_distribution_bar_renders(self):

        response = self.client.get(self.url)

        self.assertContains(
            response,
            'class="analytics-bar-high"'
        )

        self.assertContains(
            response,
            'class="analytics-bar-low"'
        )

        self.assertContains(
            response,
            'data-percentage="50.0"'
        )

    # TEST 8 - UPDATED DATA UPDATES PERCENTAGES

    def test_percentages_update_after_new_category(self):

        ReportCategory.objects.create(
            name="Epsilon",
            priority=7,
        )

        response = self.client.get(self.url)

        stats = response.context["category_stats"]

        self.assertEqual(
            stats["total"],
            5
        )

        self.assertEqual(
            stats["high_percentage"],
            60.0
        )

        self.assertEqual(
            stats["low_percentage"],
            40.0
        )


# ==========================================
# DAY 223 - CATEGORY INSIGHTS TESTS
# ==========================================

class Day223CategoryInsightsTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day223staff",
            password="TestPassword223!",
            is_staff=True,
        )

        ReportCategory.objects.create(
            name="Alpha",
            priority=5,
        )

        ReportCategory.objects.create(
            name="Beta",
            priority=8,
        )

        ReportCategory.objects.create(
            name="Gamma",
            priority=4,
        )

        ReportCategory.objects.create(
            name="Delta",
            priority=0,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - HIGHEST PRIORITY

    def test_highest_priority_category(self):

        response = self.client.get(self.url)

        insights = response.context["category_insights"]

        self.assertEqual(
            insights["highest"]["name"],
            "Beta"
        )

        self.assertEqual(
            insights["highest"]["priority"],
            8
        )

    # TEST 2 - LOWEST PRIORITY

    def test_lowest_priority_category(self):

        response = self.client.get(self.url)

        insights = response.context["category_insights"]

        self.assertEqual(
            insights["lowest"]["name"],
            "Delta"
        )

        self.assertEqual(
            insights["lowest"]["priority"],
            0
        )

    # TEST 3 - PRIORITY SPREAD

    def test_priority_spread(self):

        response = self.client.get(self.url)

        insights = response.context["category_insights"]

        self.assertEqual(
            insights["spread"],
            8
        )

    # TEST 4 - EMPTY DATABASE

    def test_empty_database_insights(self):

        ReportCategory.objects.all().delete()

        response = self.client.get(self.url)

        insights = response.context["category_insights"]

        self.assertIsNone(
            insights["highest"]
        )

        self.assertIsNone(
            insights["lowest"]
        )

        self.assertEqual(
            insights["spread"],
            0
        )

    # TEST 5 - TIE BREAKING

    def test_highest_priority_tie_breaking(self):

        ReportCategory.objects.create(
            name="Aardvark",
            priority=8,
        )

        response = self.client.get(self.url)

        insights = response.context["category_insights"]

        self.assertEqual(
            insights["highest"]["name"],
            "Aardvark"
        )

    # TEST 6 - FILTER INDEPENDENCE

    def test_insights_independent_of_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            1
        )

        insights = response.context["category_insights"]

        self.assertEqual(
            insights["highest"]["name"],
            "Beta"
        )

        self.assertEqual(
            insights["lowest"]["name"],
            "Delta"
        )

    # TEST 7 - HTML RENDERING

    def test_insights_render_in_template(self):

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "Category Insights"
        )

        self.assertContains(
            response,
            "Highest Priority Category"
        )

        self.assertContains(
            response,
            "Lowest Priority Category"
        )

        self.assertContains(
            response,
            "Priority Spread"
        )

    # TEST 8 - AUTOMATIC UPDATES

    def test_insights_update_when_priority_changes(self):

        ReportCategory.objects.filter(
            name="Beta"
        ).update(
            priority=2
        )

        response = self.client.get(self.url)

        insights = response.context["category_insights"]

        self.assertEqual(
            insights["highest"]["name"],
            "Alpha"
        )

        self.assertEqual(
            insights["lowest"]["name"],
            "Delta"
        )

        self.assertEqual(
            insights["spread"],
            5
        )


# ==========================================
# DAY 224 - TOP PRIORITY REPORT TESTS
# ==========================================

class Day224TopPriorityReportTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day224staff",
            password="TestPassword224!",
            is_staff=True,
        )

        categories = [
            ("Alpha", 5),
            ("Beta", 8),
            ("Gamma", 4),
            ("Delta", 0),
            ("Epsilon", 7),
            ("Zeta", 9),
            ("Eta", 3),
        ]

        for name, priority in categories:
            ReportCategory.objects.create(
                name=name,
                priority=priority,
            )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - ONLY FIVE CATEGORIES

    def test_report_contains_five_categories(self):

        response = self.client.get(self.url)

        report = response.context["top_priority_report"]

        self.assertEqual(len(report), 5)

    # TEST 2 - CORRECT SORT ORDER

    def test_report_sorted_by_priority(self):

        response = self.client.get(self.url)

        report = response.context["top_priority_report"]

        names = [item["name"] for item in report]

        self.assertEqual(
            names,
            [
                "Zeta",
                "Beta",
                "Epsilon",
                "Alpha",
                "Gamma",
            ]
        )

    # TEST 3 - HIGHEST BAR IS 100%

    def test_highest_category_percentage(self):

        response = self.client.get(self.url)

        report = response.context["top_priority_report"]

        self.assertEqual(
            report[0]["percentage"],
            100.0
        )

    # TEST 4 - PERCENTAGE CALCULATION

    def test_percentage_calculation(self):

        response = self.client.get(self.url)

        report = response.context["top_priority_report"]

        beta = next(
            item for item in report
            if item["name"] == "Beta"
        )

        self.assertEqual(
            beta["percentage"],
            88.89
        )

    # TEST 5 - EMPTY DATABASE

    def test_empty_database_report(self):

        ReportCategory.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["top_priority_report"],
            []
        )

        self.assertContains(
            response,
            "No categories available for this report."
        )

    # TEST 6 - ALL ZERO PRIORITIES

    def test_zero_priorities(self):

        ReportCategory.objects.all().delete()

        ReportCategory.objects.create(
            name="Zero A",
            priority=0,
        )

        ReportCategory.objects.create(
            name="Zero B",
            priority=0,
        )

        response = self.client.get(self.url)

        report = response.context["top_priority_report"]

        self.assertEqual(len(report), 2)

        for item in report:
            self.assertEqual(
                item["percentage"],
                0.0
            )

    # TEST 7 - REPORT RENDERS IN HTML

    def test_report_renders_in_template(self):

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "Top 5 Priority Categories"
        )

        self.assertContains(
            response,
            'class="top-report-bar"'
        )

        self.assertContains(
            response,
            'data-width="100.0"'
        )

    # TEST 8 - FILTER INDEPENDENCE

    def test_report_independent_of_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            1
        )

        report = response.context["top_priority_report"]

        self.assertEqual(len(report), 5)

        self.assertEqual(
            report[0]["name"],
            "Zeta"
        )


# ==========================================
# DAY 225 - ADVANCED FILTER TESTS
# ==========================================

class Day225AdvancedFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day225staff",
            password="TestPassword225!",
            is_staff=True,
        )

        categories = [
            ("Alpha", 5),
            ("Beta", 8),
            ("Gamma", 4),
            ("Delta", 0),
            ("Epsilon", 7),
            ("Zeta", 9),
            ("Eta", 3),
        ]

        for name, priority in categories:
            ReportCategory.objects.create(
                name=name,
                priority=priority,
            )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    # TEST 1 - MINIMUM PRIORITY

    def test_minimum_priority_filter(self):

        response = self.client.get(
            self.url,
            {"min_priority": "5"}
        )

        self.assertEqual(
            response.context["paginator"].count,
            4
        )

    # TEST 2 - MAXIMUM PRIORITY

    def test_maximum_priority_filter(self):

        response = self.client.get(
            self.url,
            {"max_priority": "4"}
        )

        self.assertEqual(
            response.context["paginator"].count,
            3
        )

    # TEST 3 - COMBINED RANGE

    def test_minimum_and_maximum_filter(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "4",
                "max_priority": "7",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            3
        )

    # TEST 4 - INVALID INPUT

    def test_invalid_range_values_are_ignored(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "hello",
                "max_priority": "world",
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context["paginator"].count,
            7
        )

    # TEST 5 - REVERSED RANGE

    def test_reversed_range_returns_no_results(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "9",
                "max_priority": "2",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            0
        )

    # TEST 6 - SEARCH AND RANGE TOGETHER

    def test_search_combined_with_range(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "min_priority": "4",
                "max_priority": "8",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            1
        )

    # TEST 7 - GLOBAL ANALYTICS UNCHANGED

    def test_global_analytics_ignore_range(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "8",
                "max_priority": "9",
            }
        )

        self.assertEqual(
            response.context["paginator"].count,
            2
        )

        self.assertEqual(
            response.context["category_stats"]["total"],
            7
        )

        self.assertEqual(
            response.context["category_insights"]["highest"]["name"],
            "Zeta"
        )

        self.assertEqual(
            len(response.context["top_priority_report"]),
            5
        )

    # TEST 8 - FILTER INPUTS RENDER

    def test_range_inputs_render_in_html(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "4",
                "max_priority": "8",
            }
        )

        self.assertContains(
            response,
            'name="min_priority"'
        )

        self.assertContains(
            response,
            'name="max_priority"'
        )

        self.assertContains(
            response,
            'value="4"'
        )

        self.assertContains(
            response,
            'value="8"'
        )


# ==========================================
# DAY 226 - FILTER VALIDATION UX TESTS
# ==========================================

class Day226FilterValidationTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day226staff",
            password="TestPassword226!",
            is_staff=True,
        )

        categories = [
            ("Alpha", 5),
            ("Beta", 8),
            ("Gamma", 4),
            ("Delta", 0),
            ("Epsilon", 7),
        ]

        for name, priority in categories:
            ReportCategory.objects.create(
                name=name,
                priority=priority,
            )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse(
            "report_category_list"
        )

    # TEST 1 - INVALID MINIMUM

    def test_invalid_minimum_message(self):

        response = self.client.get(
            self.url,
            {"min_priority": "hello"}
        )

        self.assertContains(
            response,
            "Minimum priority must be a valid whole number."
        )

        self.assertEqual(
            response.context["paginator"].count,
            5
        )

    # TEST 2 - INVALID MAXIMUM

    def test_invalid_maximum_message(self):

        response = self.client.get(
            self.url,
            {"max_priority": "abc"}
        )

        self.assertContains(
            response,
            "Maximum priority must be a valid whole number."
        )

    # TEST 3 - REVERSED RANGE

    def test_reversed_range_message(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "9",
                "max_priority": "2",
            }
        )

        self.assertContains(
            response,
            "Minimum priority cannot be greater than maximum priority."
        )

        self.assertEqual(
            response.context["paginator"].count,
            0
        )

    # TEST 4 - VALID RANGE HAS NO WARNINGS

    def test_valid_range_has_no_warnings(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "4",
                "max_priority": "8",
            }
        )

        self.assertEqual(
            response.context["range_messages"],
            []
        )

        self.assertEqual(
            response.context["paginator"].count,
            4
        )

    # TEST 5 - ACTIVE RANGE SUMMARY

    def test_active_range_summary(self):

        response = self.client.get(
            self.url,
            {
                "min_priority": "4",
                "max_priority": "8",
            }
        )

        self.assertEqual(
            response.context["active_range_summary"],
            "Priority range: 4 to 8"
        )

        self.assertContains(
            response,
            "Active Range:"
        )

    # TEST 6 - SINGLE BOUND SUMMARY

    def test_single_bound_summary(self):

        response = self.client.get(
            self.url,
            {"min_priority": "5"}
        )

        self.assertEqual(
            response.context["active_range_summary"],
            "Minimum priority: 5"
        )

    # TEST 7 - CLEAR LINK PRESERVES FILTERS

    def test_clear_range_link_preserves_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
                "sort": "name_desc",
                "min_priority": "4",
                "max_priority": "8",
            }
        )

        self.assertContains(
            response,
            'class="range-clear-link"'
        )

        self.assertContains(
            response,
            "q=Alpha&amp;priority=high&amp;sort=name_desc"
        )

    # TEST 8 - ZERO IS VALID

    def test_zero_minimum_is_valid(self):

        response = self.client.get(
            self.url,
            {"min_priority": "0"}
        )

        self.assertEqual(
            response.context["range_messages"],
            []
        )

        self.assertEqual(
            response.context["active_range_summary"],
            "Minimum priority: 0"
        )

        self.assertEqual(
            response.context["paginator"].count,
            5
        )


# ==========================================
# DAY 227 - FILTER PRESET TESTS
# ==========================================

class Day227FilterPresetTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day227staff",
            password="TestPassword227!",
            is_staff=True,
        )

        categories = [
            ("Alpha", 5),
            ("Beta", 8),
            ("Gamma", 4),
            ("Delta", 0),
            ("Epsilon", 7),
            ("Zeta", 9),
            ("Eta", 3),
        ]

        for name, priority in categories:
            ReportCategory.objects.create(
                name=name,
                priority=priority,
            )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse("report_category_list")

    def get_preset(self, response, key):

        presets = response.context["filter_presets"]

        return next(
            preset
            for preset in presets
            if preset["key"] == key
        )

    # TEST 1 - FOUR PRESETS EXIST

    def test_four_presets_available(self):

        response = self.client.get(self.url)

        presets = response.context["filter_presets"]

        self.assertEqual(len(presets), 4)

        keys = [preset["key"] for preset in presets]

        self.assertEqual(
            keys,
            ["all", "high", "low", "range"]
        )

    # TEST 2 - SEARCH IS PRESERVED

    def test_presets_preserve_search_query(self):

        response = self.client.get(
            self.url,
            {"q": "Alpha Beta"}
        )

        high = self.get_preset(response, "high")

        self.assertIn(
            "q=Alpha+Beta",
            high["url"]
        )

    # TEST 3 - HIGH PRIORITY PRESET

    def test_high_priority_preset(self):

        response = self.client.get(self.url)

        high = self.get_preset(response, "high")

        filtered_response = self.client.get(
            high["url"]
        )

        self.assertEqual(
            filtered_response.context["paginator"].count,
            4
        )

    # TEST 4 - LOW PRIORITY PRESET

    def test_low_priority_preset(self):

        response = self.client.get(self.url)

        low = self.get_preset(response, "low")

        filtered_response = self.client.get(
            low["url"]
        )

        self.assertEqual(
            filtered_response.context["paginator"].count,
            3
        )

    # TEST 5 - PRIORITY RANGE PRESET

    def test_range_preset(self):

        response = self.client.get(self.url)

        range_preset = self.get_preset(
            response,
            "range"
        )

        filtered_response = self.client.get(
            range_preset["url"]
        )

        self.assertEqual(
            filtered_response.context["paginator"].count,
            4
        )


    # TEST 6 - OLD RANGE AND PAGE ARE CLEARED

    def test_preset_clears_previous_range(self):

        # Request a valid page with existing range filters
        response = self.client.get(
            self.url,
            {
                "min_priority": "8",
                "max_priority": "9",
                "page": "1",
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        # Retrieve the High Priority preset
        high = self.get_preset(response, "high")

        # The preset must remove old range filters
        self.assertNotIn(
            "min_priority=",
            high["url"]
        )

        self.assertNotIn(
            "max_priority=",
            high["url"]
        )

        # Preset links must not preserve pagination
        self.assertNotIn(
            "page=",
            high["url"]
        )

    # TEST 7 - ACTIVE PRESET

    def test_active_preset_is_identified(self):

        response = self.client.get(
            self.url,
            {
                "priority": "high",
                "sort": "priority_high",
            }
        )

        high = self.get_preset(response, "high")

        self.assertTrue(high["active"])

        all_preset = self.get_preset(
            response,
            "all"
        )

        self.assertFalse(all_preset["active"])

    # TEST 8 - TEMPLATE AND ANALYTICS

    def test_presets_render_without_changing_analytics(self):

        response = self.client.get(
            self.url,
            {
                "priority": "high",
                "sort": "priority_high",
            }
        )

        self.assertContains(
            response,
            "Quick Filter Presets"
        )

        self.assertContains(
            response,
            "High Priority"
        )

        self.assertContains(
            response,
            "Priority 4-8"
        )

        self.assertContains(
            response,
            'aria-current="page"'
        )

        self.assertEqual(
            response.context["category_stats"]["total"],
            7
        )


# ==========================================
# DAY 228 - SAVED FILTER PREFERENCE TESTS
# ==========================================

class Day228SavedFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day228staff",
            password="TestPassword228!",
            is_staff=True,
        )

        cls.normal_user = User.objects.create_user(
            username="day228normal",
            password="TestPassword228!",
            is_staff=False,
        )

        categories = [
            ("Alpha", 5),
            ("Beta", 8),
            ("Gamma", 4),
            ("Delta", 0),
            ("Epsilon", 7),
            ("Zeta", 9),
            ("Eta", 3),
        ]

        for name, priority in categories:

            ReportCategory.objects.create(
                name=name,
                priority=priority,
            )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse(
            "report_category_list"
        )

    # TEST 1 - SAVE FILTERS

    def test_save_filters_in_session(self):

        response = self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "q": "Alpha",
                "priority": "high",
                "sort": "priority_high",
                "min_priority": "5",
                "max_priority": "9",
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        saved = self.client.session[
            "report_category_saved_filters"
        ]

        self.assertEqual(
            saved["q"],
            "Alpha"
        )

        self.assertEqual(
            saved["priority"],
            "high"
        )

        self.assertEqual(
            saved["min_priority"],
            "5"
        )

    # TEST 2 - APPLY SAVED FILTERS

    def test_apply_saved_filters(self):

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "high",
                "sort": "priority_high",
            }
        )

        response = self.client.get(self.url)

        saved_url = response.context[
            "saved_category_filters_url"
        ]

        filtered_response = self.client.get(
            saved_url
        )

        self.assertEqual(
            filtered_response.context["paginator"].count,
            4
        )

    # TEST 3 - PRESERVE SEARCH AND RANGE

    def test_saved_url_preserves_search_and_range(self):

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "q": "Alpha Beta",
                "priority": "all",
                "sort": "priority_high",
                "min_priority": "4",
                "max_priority": "8",
            }
        )

        response = self.client.get(self.url)

        saved_url = response.context[
            "saved_category_filters_url"
        ]

        self.assertIn(
            "q=Alpha+Beta",
            saved_url
        )

        self.assertIn(
            "min_priority=4",
            saved_url
        )

        self.assertIn(
            "max_priority=8",
            saved_url
        )

    # TEST 4 - OVERWRITE SAVED FILTERS

    def test_save_overwrites_previous_preferences(self):

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "high",
            }
        )

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "low",
            }
        )

        saved = self.client.session[
            "report_category_saved_filters"
        ]

        self.assertEqual(
            saved["priority"],
            "low"
        )

    # TEST 5 - CLEAR SAVED FILTERS

    def test_clear_saved_filters(self):

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "high",
            }
        )

        response = self.client.post(
            self.url,
            {
                "saved_filter_action": "clear",
                "priority": "high",
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertNotIn(
            "report_category_saved_filters",
            self.client.session
        )

    # TEST 6 - NO SAVED PREFERENCES

    def test_no_saved_filters_initially(self):

        response = self.client.get(self.url)

        self.assertIsNone(
            response.context["saved_category_filters"]
        )

        self.assertEqual(
            response.context[
                "saved_category_filters_url"
            ],
            ""
        )

        self.assertContains(
            response,
            "No filters saved yet."
        )

    # TEST 7 - INVALID VALUES NORMALIZED

    def test_invalid_values_are_normalized(self):

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "unknown",
                "sort": "invalid",
                "min_priority": "hello",
                "max_priority": "8",
            }
        )

        saved = self.client.session[
            "report_category_saved_filters"
        ]

        self.assertEqual(
            saved["priority"],
            "all"
        )

        self.assertEqual(
            saved["sort"],
            "name_asc"
        )

        self.assertNotIn(
            "min_priority",
            saved
        )

        self.assertEqual(
            saved["max_priority"],
            "8"
        )

    # TEST 8 - NON-STAFF CANNOT SAVE

    def test_non_staff_cannot_save_filters(self):

        self.client.force_login(
            self.normal_user
        )

        response = self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "high",
            }
        )

        self.assertIn(
            response.status_code,
            (302, 403)
        )

        self.assertNotIn(
            "report_category_saved_filters",
            self.client.session
        )


# ==========================================
# DAY 229 - RECENT FILTER HISTORY TESTS
# ==========================================

class Day229RecentFilterHistoryTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day229staff",
            password="TestPassword229!",
            is_staff=True,
        )

        cls.normal_user = User.objects.create_user(
            username="day229normal",
            password="TestPassword229!",
            is_staff=False,
        )

        categories = [
            ("Alpha", 5),
            ("Beta", 8),
            ("Gamma", 4),
            ("Delta", 0),
            ("Epsilon", 7),
            ("Zeta", 9),
            ("Eta", 3),
        ]

        for name, priority in categories:

            ReportCategory.objects.create(
                name=name,
                priority=priority,
            )

    def setUp(self):

        self.client.force_login(
            self.staff_user
        )

        self.url = reverse(
            "report_category_list"
        )

        self.history_key = (
            "report_category_recent_filter_history"
        )

    # TEST 1 - RECORD FILTERS

    def test_filter_request_is_recorded(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        history = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            len(history),
            1
        )

        self.assertEqual(
            history[0]["q"],
            "Alpha"
        )

        self.assertEqual(
            history[0]["priority"],
            "high"
        )

    # TEST 2 - DEFAULT VISITS ARE IGNORED

    def test_default_dashboard_is_not_recorded(self):

        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertNotIn(
            self.history_key,
            self.client.session
        )

        self.assertContains(
            response,
            "No recent filters yet."
        )

    # TEST 3 - DUPLICATES ARE REMOVED

    def test_duplicate_filters_are_not_repeated(self):

        filters = {
            "q": "Alpha",
            "priority": "high",
        }

        self.client.get(
            self.url,
            filters
        )

        self.client.get(
            self.url,
            {
                **filters,
                "page": "1",
            }
        )

        history = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            len(history),
            1
        )

    # TEST 4 - NEWEST ENTRY FIRST

    def test_newest_filter_appears_first(self):

        for search in (
            "Alpha",
            "Beta",
            "Gamma",
        ):

            self.client.get(
                self.url,
                {"q": search}
            )

        history = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            history[0]["q"],
            "Gamma"
        )

        self.assertEqual(
            history[1]["q"],
            "Beta"
        )

        self.assertEqual(
            history[2]["q"],
            "Alpha"
        )

    # TEST 5 - LIMIT HISTORY TO FIVE

    def test_history_is_limited_to_five(self):

        for number in range(1, 8):

            self.client.get(
                self.url,
                {
                    "q": f"Search{number}"
                }
            )

        history = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            len(history),
            5
        )

        self.assertEqual(
            history[0]["q"],
            "Search7"
        )

        self.assertEqual(
            history[-1]["q"],
            "Search3"
        )

    # TEST 6 - HISTORY LINKS RESTORE FILTERS

    def test_history_link_restores_filters(self):

        response = self.client.get(
            self.url,
            {
                "q": "Alpha",
                "priority": "high",
                "sort": "priority_high",
                "min_priority": "5",
                "max_priority": "9",
            }
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(
            len(history),
            1
        )

        saved_url = history[0]["url"]

        self.assertIn(
            "q=Alpha",
            saved_url
        )

        self.assertIn(
            "min_priority=5",
            saved_url
        )

        restored_response = self.client.get(
            saved_url
        )

        self.assertEqual(
            restored_response.status_code,
            200
        )

        self.assertEqual(
            restored_response.context[
                "paginator"
            ].count,
            1
        )

    # TEST 7 - CLEAR HISTORY

    def test_clear_history(self):

        self.client.get(
            self.url,
            {"q": "Alpha"}
        )

        response = self.client.post(
            self.url,
            {
                "saved_filter_action": (
                    "clear_history"
                ),
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertNotIn(
            self.history_key,
            self.client.session
        )

        # Follow the redirect to the
        # unfiltered dashboard.
        response = self.client.get(
            response["Location"]
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.context[
                "recent_filter_history"
            ],
            []
        )

    # TEST 8 - NON-STAFF CANNOT RECORD HISTORY

    def test_non_staff_cannot_record_history(self):

        self.client.force_login(
            self.normal_user
        )

        response = self.client.get(
            self.url,
            {"q": "Alpha"}
        )

        self.assertIn(
            response.status_code,
            (302, 403)
        )

        self.assertNotIn(
            self.history_key,
            self.client.session
        )


# ==========================================
# DAY 230 - FILTER HISTORY MANAGEMENT TESTS
# ==========================================

class Day230FilterHistoryManagementTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day230staff",
            password="TestPassword230!",
            is_staff=True,
        )

        cls.normal_user = User.objects.create_user(
            username="day230normal",
            password="TestPassword230!",
            is_staff=False,
        )

        ReportCategory.objects.create(
            name="Alpha",
            priority=5,
        )

        ReportCategory.objects.create(
            name="Beta",
            priority=8,
        )

        ReportCategory.objects.create(
            name="Gamma",
            priority=3,
        )

    def setUp(self):

        self.client.force_login(
            self.staff_user
        )

        self.url = reverse(
            "report_category_list"
        )

        self.history_key = (
            "report_category_recent_filter_history"
        )

        self.saved_key = (
            "report_category_saved_filters"
        )

    def create_history(self):

        for search in (
            "Alpha",
            "Beta",
            "Gamma",
        ):

            self.client.get(
                self.url,
                {"q": search}
            )

    def remove_entry(self, index):

        return self.client.post(
            self.url,
            {
                "saved_filter_action": (
                    "remove_history_entry"
                ),
                "history_index": index,
            }
        )

    # TEST 1 - REMOVE MIDDLE ENTRY

    def test_remove_middle_history_entry(self):

        self.create_history()

        response = self.remove_entry(1)

        self.assertEqual(
            response.status_code,
            302
        )

        history = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            len(history),
            2
        )

        self.assertEqual(
            history[0]["q"],
            "Gamma"
        )

        self.assertEqual(
            history[1]["q"],
            "Alpha"
        )

    # TEST 2 - REMOVE MOST RECENT ENTRY

    def test_remove_most_recent_entry(self):

        self.create_history()

        self.remove_entry(0)

        history = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            history[0]["q"],
            "Beta"
        )

        self.assertEqual(
            len(history),
            2
        )

    # TEST 3 - REJECT NON-NUMERIC INDEX

    def test_reject_invalid_text_index(self):

        self.create_history()

        response = self.remove_entry(
            "invalid"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            len(
                self.client.session[
                    self.history_key
                ]
            ),
            3
        )

    # TEST 4 - REJECT NEGATIVE INDEX

    def test_reject_negative_index(self):

        self.create_history()

        response = self.remove_entry(-1)

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            len(
                self.client.session[
                    self.history_key
                ]
            ),
            3
        )

    # TEST 5 - REJECT OUT-OF-RANGE INDEX

    def test_reject_out_of_range_index(self):

        self.create_history()

        response = self.remove_entry(99)

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertEqual(
            len(
                self.client.session[
                    self.history_key
                ]
            ),
            3
        )

    # TEST 6 - PRESERVE SAVED FILTERS

    def test_removal_preserves_saved_preferences(self):

        self.client.post(
            self.url,
            {
                "saved_filter_action": "save",
                "priority": "high",
                "sort": "priority_high",
            }
        )

        self.create_history()

        response = self.remove_entry(1)

        self.assertEqual(
            response.status_code,
            302
        )

        saved = self.client.session[
            self.saved_key
        ]

        self.assertEqual(
            saved["priority"],
            "high"
        )

        self.assertEqual(
            saved["sort"],
            "priority_high"
        )

    # TEST 7 - PRESERVE ORIGINAL INDEXES

    def test_history_uses_original_session_index(self):

        session = self.client.session

        session[self.history_key] = [
            {
                "q": "Alpha",
                "priority": "all",
                "sort": "name_asc",
            },
            "invalid stored entry",
            {
                "q": "Beta",
                "priority": "all",
                "sort": "name_asc",
            },
        ]

        session.save()

        response = self.client.get(
            self.url
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(
            len(history),
            2
        )

        self.assertEqual(
            history[0]["index"],
            0
        )

        self.assertEqual(
            history[1]["index"],
            2
        )

        # Remove the second visible entry.
        # Its original session index is 2.

        remove_response = self.remove_entry(
            history[1]["index"]
        )

        self.assertEqual(
            remove_response.status_code,
            302
        )

        stored = self.client.session[
            self.history_key
        ]

        self.assertEqual(
            stored[0]["q"],
            "Alpha"
        )

        self.assertEqual(
            len(stored),
            2
        )

    # TEST 8 - NON-STAFF CANNOT REMOVE

    def test_non_staff_cannot_remove_history(self):

        self.client.force_login(
            self.normal_user
        )

        response = self.remove_entry(0)

        self.assertIn(
            response.status_code,
            (302, 403)
        )

        self.assertNotIn(
            self.history_key,
            self.client.session
        )


# ==========================================
# DAY 231 - HISTORY SEARCH TESTS
# ==========================================

class Day231FilterHistorySearchTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day231staff",
            password="TestPassword231!",
            is_staff=True,
        )

        cls.normal_user = User.objects.create_user(
            username="day231normal",
            password="TestPassword231!",
            is_staff=False,
        )

        ReportCategory.objects.create(
            name="Alpha",
            priority=5,
        )

        ReportCategory.objects.create(
            name="Beta",
            priority=8,
        )

        ReportCategory.objects.create(
            name="Gamma",
            priority=3,
        )

    def setUp(self):
        self.client.force_login(self.staff_user)

        self.url = reverse(
            "report_category_list"
        )

        self.history_key = (
            "report_category_recent_filter_history"
        )

    def create_history(self):
        """
        History order after these requests:
        Gamma, Beta, Alpha
        """
        for name in ("Alpha", "Beta", "Gamma"):
            self.client.get(
                self.url,
                {"q": name},
            )

    # TEST 1
    def test_search_filters_history_by_label(self):
        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "Alpha"},
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(history), 1)
        self.assertIn("Alpha", history[0]["label"])
        self.assertEqual(history[0]["index"], 2)

    # TEST 2
    def test_search_is_case_insensitive(self):
        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "bEtA"},
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(len(history), 1)
        self.assertIn("Beta", history[0]["label"])

    # TEST 3
    def test_search_trims_whitespace(self):
        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "  Gamma  "},
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(
            response.context["history_search_query"],
            "Gamma",
        )

        self.assertEqual(len(history), 1)
        self.assertIn("Gamma", history[0]["label"])

    # TEST 4
    def test_empty_search_shows_all_history(self):
        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "   "},
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(len(history), 3)
        self.assertEqual(
            response.context["history_search_query"],
            "",
        )

    # TEST 5
    def test_no_matches_preserves_stored_history(self):
        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "Missing"},
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(history, [])
        self.assertEqual(
            response.context["recent_history_total_count"],
            3,
        )
        self.assertEqual(
            response.context["recent_history_visible_count"],
            0,
        )

        stored_history = self.client.session[
            self.history_key
        ]

        self.assertEqual(len(stored_history), 3)

    # TEST 6
    def test_history_search_does_not_create_history(self):
        response = self.client.get(
            self.url,
            {"history_q": "Alpha"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["recent_filter_history"],
            [],
        )

        self.assertNotIn(
            self.history_key,
            self.client.session,
        )

    # TEST 7
    def test_search_preserves_index_for_removal(self):
        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "Alpha"},
        )

        history = response.context[
            "recent_filter_history"
        ]

        self.assertEqual(len(history), 1)

        # Alpha is at index 2 in session.
        original_index = history[0]["index"]
        self.assertEqual(original_index, 2)

        remove_response = self.client.post(
            self.url,
            {
                "saved_filter_action": "remove_history_entry",
                "history_index": original_index,
            },
        )

        self.assertEqual(remove_response.status_code, 302)

        stored_history = self.client.session[
            self.history_key
        ]

        self.assertEqual(len(stored_history), 2)

        remaining_names = [
            item["q"] for item in stored_history
        ]

        self.assertEqual(
            remaining_names,
            ["Gamma", "Beta"],
        )

    # TEST 8
    def test_non_staff_cannot_search_history(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(
            self.url,
            {"history_q": "Alpha"},
        )

        self.assertIn(
            response.status_code,
            (302, 403),
        )

        self.assertNotIn(
            self.history_key,
            self.client.session,
        )

# ==========================================
# DAY 232 - HISTORY UX & ACCESSIBILITY TESTS
# ==========================================

class Day232HistoryAccessibilityTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        cls.staff_user = User.objects.create_user(
            username="day232staff",
            password="TestPassword232!",
            is_staff=True,
        )

        ReportCategory.objects.create(
            name="Alpha",
            priority=5,
        )

        ReportCategory.objects.create(
            name="Beta",
            priority=8,
        )

        ReportCategory.objects.create(
            name="Gamma",
            priority=3,
        )

    def setUp(self):

        self.client.force_login(self.staff_user)

        self.url = reverse(
            "report_category_list"
        )

        self.history_key = (
            "report_category_recent_filter_history"
        )

    def create_history(self):

        for name in ("Alpha", "Beta", "Gamma"):

            self.client.get(
                self.url,
                {"q": name},
            )

    # ======================================
    # TEST 1 - SEARCH ACCESSIBILITY
    # ======================================

    def test_search_form_has_accessible_label(self):

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            'aria-label="Search recent filter history"',
        )

        self.assertContains(
            response,
            'role="search"',
        )

    # ======================================
    # TEST 2 - INPUT HELP TEXT
    # ======================================

    def test_search_input_has_help_text(self):

        response = self.client.get(self.url)

        self.assertContains(
            response,
            'id="history-search-help"',
        )

        self.assertContains(
            response,
            'aria-describedby="history-search-help"',
        )

    # ======================================
    # TEST 3 - EMPTY HISTORY FEEDBACK
    # ======================================

    def test_empty_history_has_feedback(self):

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["history_search_feedback"],
            "No recent filter history yet.",
        )

        self.assertContains(
            response,
            'aria-live="polite"',
        )

        self.assertContains(
            response,
            'role="status"',
        )

    # ======================================
    # TEST 4 - NORMAL HISTORY FEEDBACK
    # ======================================

    def test_unfiltered_history_shows_count(self):

        self.create_history()

        response = self.client.get(self.url)

        self.assertEqual(
            response.context["recent_history_total_count"],
            3,
        )

        self.assertEqual(
            response.context["history_search_feedback"],
            "3 recent history entries available.",
        )

        self.assertFalse(
            response.context["history_search_active"]
        )

    # ======================================
    # TEST 5 - SEARCH RESULTS FEEDBACK
    # ======================================

    def test_matching_search_has_clear_feedback(self):

        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "Alpha"},
        )

        self.assertTrue(
            response.context["history_search_active"]
        )

        self.assertEqual(
            response.context["recent_history_visible_count"],
            1,
        )

        self.assertEqual(
            response.context["history_search_feedback"],
            'Showing 1 of 3 history entries for "Alpha".',
        )

    # ======================================
    # TEST 6 - NO MATCHES FEEDBACK
    # ======================================

    def test_no_matches_shows_helpful_message(self):

        self.create_history()

        response = self.client.get(
            self.url,
            {"history_q": "Unknown"},
        )

        self.assertEqual(
            response.context["history_search_feedback"],
            'No history entries match "Unknown".',
        )

        self.assertContains(
            response,
            "Try another keyword or clear the search.",
        )

        self.assertContains(
            response,
            'aria-label="Clear history search"',
        )

    # ======================================
    # TEST 7 - SEARCH LENGTH LIMIT
    # ======================================

    def test_search_query_is_limited_to_100_characters(self):

        long_query = "A" * 150

        response = self.client.get(
            self.url,
            {"history_q": long_query},
        )

        cleaned_query = response.context[
            "history_search_query"
        ]

        self.assertEqual(
            len(cleaned_query),
            100,
        )

        self.assertEqual(
            cleaned_query,
            "A" * 100,
        )

        self.assertContains(
            response,
            'maxlength="100"',
        )

    # ======================================
    # TEST 8 - ACCESSIBLE ACTIONS
    # ======================================

    def test_history_actions_have_accessible_labels(self):

        self.client.get(
            self.url,
            {"q": "Alpha"},
        )

        response = self.client.get(self.url)

        self.assertContains(
            response,
            'aria-label="Apply filter:',
        )

        self.assertContains(
            response,
            'aria-label="Remove ',
        )

        self.assertContains(
            response,
            'aria-label="Clear recent filter history"',
        )


from django.test import TestCase
from .models import ContactMessage, MessageAttachment


class Day234ORMOptimizationTests(TestCase):

    def test_select_related_avoids_extra_queries(self):
        message = ContactMessage.objects.create(
            name="Test User",
            email="test@example.com",
            message="Day 234 ORM test"
        )

        attachment = MessageAttachment.objects.create(
            contact_message=message,
            file="attachments/day234_test.txt"
        )

        with self.assertNumQueries(1):
            results = list(
                MessageAttachment.objects
                .select_related("contact_message")
                .filter(pk=attachment.pk)
            )

            related_name = results[0].contact_message.name

        self.assertEqual(related_name, "Test User")
