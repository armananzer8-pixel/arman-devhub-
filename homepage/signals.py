
# ============================================
# ARMAN DEVHUB - DJANGO SIGNALS
# DAY 176 + DAY 190
# ============================================

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import DeveloperProfile, MessageAttachment


# ============================================
# DAY 176 - AUTOMATIC PROFILE CREATION
# ============================================

@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL
)
def create_developer_profile(
    sender,
    instance,
    created,
    raw=False,
    **kwargs
):

    # Ignore fixture-loading events
    if raw:
        return

    # Create profile only for new users
    if created:

        DeveloperProfile.objects.get_or_create(
            user=instance
        )


# ============================================
# DAY 190 - AUTOMATIC FILE CLEANUP
# ============================================

@receiver(
    post_delete,
    sender=MessageAttachment,
    dispatch_uid="homepage_cleanup_attachment_file"
)
def cleanup_attachment_file(
    sender,
    instance,
    using,
    **kwargs
):

    file_name = instance.file.name

    if not file_name:
        return

    storage = instance.file.storage

    def delete_file_after_commit():

        # Check if another attachment
        # references the same file.
        still_in_use = (
            MessageAttachment.objects.using(using)
            .filter(file=file_name)
            .exists()
        )

        if not still_in_use:
            storage.delete(file_name)

    # Wait until database transaction commits.
    transaction.on_commit(
        delete_file_after_commit,
        using=using
    )
