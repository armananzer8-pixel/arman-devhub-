from django import forms
from .models import DeveloperProfile

from .models import ContactMessage, DeveloperProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# =====================================
# CONTACT FORM
# =====================================

class ContactForm(forms.Form):

    name = forms.CharField(
        max_length=50,
        label="Your Name"
    )

    email = forms.EmailField(
        required=True,
        label="Your Email"
    )

    message = forms.CharField(
        label="Your Message",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Enter your message here"
            }
        )
    )


# =====================================
# SIGNUP FORM
# =====================================

class SignupForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="Email Address"
    )

    class Meta:
        model = User

        fields = (
            "username",
            "email",
            "password1",
            "password2"
        )


# =====================================
# USER PROFILE EDIT FORM - DAY 165
# =====================================

class ProfileForm(forms.ModelForm):

    email = forms.EmailField(
        required=True,
        label="Email Address"
    )

    class Meta:
        model = User

        fields = (
            "first_name",
            "last_name",
            "email"
        )

        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
        }

        # =====================================
# DAY 175 - DEVELOPER PROFILE FORM
# =====================================

class DeveloperProfileForm(forms.ModelForm):

    class Meta:
        model = DeveloperProfile

        fields = [
            "bio",
            "favorite_language"
        ]

        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell us about your skills"
                }
            ),

            "favorite_language": forms.TextInput(
                attrs={
                    "placeholder": "Example: Python"
                }
            )
        }


from django import forms
from django.core.exceptions import ValidationError

from .models import ContactMessage


# =====================================
# DAY 185 - CUSTOM MODEL FORM
# =====================================

class StaffContactMessageForm(forms.ModelForm):

    class Meta:

        model = ContactMessage

        fields = [
            "name",
            "email",
            "message",
        ]

        labels = {
            "name": "Sender Name",
            "email": "Email Address",
            "message": "Your Message",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter sender's name"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "example@email.com"
                }
            ),

            "message": forms.Textarea(
                attrs={
                    "placeholder": "Write your message here",
                    "rows": 5,
                }
            ),
        }

        error_messages = {
            "name": {
                "required": "Please enter the sender's name.",
            },

            "email": {
                "required": "Please enter an email address.",
                "invalid": "Please enter a valid email address.",
            },

            "message": {
                "required": "Please write a message.",
            },
        }

    # =================================
    # VALIDATE THE NAME FIELD
    # =================================

    def clean_name(self):

        name = self.cleaned_data["name"].strip()

        if len(name) < 2:

            raise ValidationError(
                "Name must contain at least 2 characters.",
                code="too_short"
            )

        return name

    # =================================
    # VALIDATE THE MESSAGE FIELD
    # =================================

    def clean_message(self):

        message = self.cleaned_data["message"].strip()

        if len(message) < 10:

            raise ValidationError(
                "Message must be at least 10 characters long.",
                code="too_short"
            )

        return message

    # =================================
    # VALIDATE MULTIPLE FIELDS TOGETHER
    # =================================

    def clean(self):

        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        message = cleaned_data.get("message")

        if name and message:

            if name.casefold() == message.casefold():

                raise ValidationError(
                    "Message cannot be identical to the sender's name.",
                    code="duplicate_content"
                )

        return cleaned_data


# =====================================
# DAY 186 - MESSAGE NOTE FORM
# =====================================

from django import forms


class MessageNoteForm(forms.Form):

    note = forms.CharField(
        label="Staff Note",
        min_length=3,
        max_length=1000,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Write a note about this message..."
            }
        ),
        error_messages={
            "required": "Please enter a note.",
            "min_length": "Note must contain at least 3 characters.",
        }
    )



# =====================================
# DAY 188 - ATTACHMENT UPLOAD FORM
# =====================================

from pathlib import Path

from django import forms

from .models import MessageAttachment


MAX_ATTACHMENT_SIZE = 1024 * 1024  # 1 MB


class MessageAttachmentForm(forms.ModelForm):

    class Meta:

        model = MessageAttachment

        fields = ["file"]

        labels = {
            "file": "Choose Attachment",
        }

        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "accept": ".txt,.pdf"
                }
            )
        }

    def clean_file(self):

        uploaded_file = self.cleaned_data["file"]

        # Check file size
        if uploaded_file.size > MAX_ATTACHMENT_SIZE:

            raise forms.ValidationError(
                "File size must not exceed 1 MB."
            )

        extension = Path(
            uploaded_file.name
        ).suffix.lower()

        # Allow only two file types
        if extension not in [".txt", ".pdf"]:

            raise forms.ValidationError(
                "Only PDF and TXT files are allowed."
            )

        # Read at most 1 MB after the size check.
        content = uploaded_file.read()

        # Basic PDF file signature check
        if extension == ".pdf":

            if not content.startswith(b"%PDF-"):

                raise forms.ValidationError(
                    "The selected file is not a valid PDF."
                )

        # Check text files can be decoded as UTF-8
        if extension == ".txt":

            try:
                content.decode("utf-8")

            except UnicodeDecodeError:

                raise forms.ValidationError(
                    "TXT files must contain UTF-8 text."
                )

        # Reset the pointer before Django saves it
        uploaded_file.seek(0)

        return uploaded_file



# ===========================================
# DAY 191 - REPLACE ATTACHMENT FORM
# ===========================================

class MessageAttachmentReplaceForm(MessageAttachmentForm):

    class Meta(MessageAttachmentForm.Meta):
        fields = ["file"]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Replacing a file requires a new upload.
        self.fields["file"].required = True
