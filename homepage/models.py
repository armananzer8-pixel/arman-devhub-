from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from django.conf import settings
from django.db import models
from django.db.models import Q

# =====================================
# DAY 177 - CUSTOM QUERYSET
# =====================================

class ContactMessageQuerySet(models.QuerySet):

    # Search name, email, and message
    def search(self, query):

        query = (query or "").strip()

        if not query:
            return self

        return self.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(message__icontains=query)
        )

    # Filter messages by a specific tag
    def with_tag(self, tag_name):

        return self.filter(
            tags__name__iexact=tag_name
        ).distinct()

    # Show newest messages first
    def newest(self):

        return self.order_by(
            "-created_at",
            "-id"
        )

class ContactMessage(models.Model):

    name = models.CharField(max_length=50)

    email = models.EmailField(blank=True)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # DAY 174 - ADD THIS FIELD
    tags = models.ManyToManyField(
        "MessageTag",
        blank=True,
        related_name="contact_messages"
    )

    objects = ContactMessageQuerySet.as_manager()

    def __str__(self):
        return self.name

# =====================================
# DAY 173 - MESSAGE NOTE MODEL
# =====================================

class MessageNote(models.Model):

    # One contact message can have many notes
    contact_message = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    note = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Note for {self.contact_message.name}"

    # =====================================
# DAY 174 - MESSAGE TAG MODEL
# =====================================

class MessageTag(models.Model):

    name = models.CharField(
        max_length=50,
        unique=True
    )

    def __str__(self):
        return self.name

    # =====================================
# DAY 175 - ONE TO ONE RELATIONSHIP
# =====================================

class DeveloperProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="developer_profile"
    )

    bio = models.TextField(
        max_length=300,
        blank=True
    )

    favorite_language = models.CharField(
        max_length=50,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Developer Profile - {self.user.username}"


# =====================================
# DAY 188 - MESSAGE ATTACHMENTS
# =====================================

class MessageAttachment(models.Model):

    contact_message = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    file = models.FileField(
        upload_to="message_attachments/"
    )

    uploaded_at = models.DateTimeField(
    auto_now_add=True,
    db_index=True
)

    def __str__(self):

        return (
            f"Attachment for message "
            f"{self.contact_message_id}"
        )



# ==========================================
# DAY 214 - MODEL VALIDATION
# ==========================================

def validate_report_category_name(value):
    """
    A category name must contain at least
    3 non-whitespace characters.
    """
    if len(value.strip()) < 3:
        raise ValidationError(
            "Category name must contain at least 3 characters."
        )


class ReportCategory(models.Model):

    name = models.CharField(
        max_length=80,
        validators=[validate_report_category_name],
    )

    priority = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    def clean(self):
        super().clean()

        # Archived categories must have priority 0.
        if (
            self.name.strip().lower() == "archived"
            and self.priority != 0
        ):
            raise ValidationError({
                "priority": "Archived categories must have priority 0."
            })

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                name="unique_report_category_name",
            ),
            models.CheckConstraint(
                condition=models.Q(priority__gte=0),
                name="report_category_priority_nonnegative",
            ),
        ]

    def __str__(self):
        return self.name
