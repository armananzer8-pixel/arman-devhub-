from django.contrib import admin
from .models import ContactMessage, MessageNote, MessageTag, DeveloperProfile


# Day 173 - Message Notes Inline
class MessageNoteInline(admin.TabularInline):
    model = MessageNote
    extra = 1


# Existing Contact Message Admin
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "message",
    )

    # THIS LINE IS VERY IMPORTANT
    inlines = [MessageNoteInline]

 # DAY 174 - MESSAGE TAGS
    filter_horizontal = ("tags",)

# Separate Message Notes Admin
@admin.register(MessageNote)
class MessageNoteAdmin(admin.ModelAdmin):

    list_display = (
        "contact_message",
        "created_at",
    )

    # =====================================
# DAY 174 - MESSAGE TAG ADMIN
# =====================================

@admin.register(MessageTag)
class MessageTagAdmin(admin.ModelAdmin):

    list_display = ("name",)

    search_fields = ("name",)

    # =====================================
# DAY 175 - DEVELOPER PROFILE ADMIN
# =====================================

@admin.register(DeveloperProfile)
class DeveloperProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "favorite_language",
        "created_at"
    )

    search_fields = (
        "user__username",
        "favorite_language"
    )