
# ==========================================
# DAY 215 - ADVANCED DJANGO FORM VALIDATION
# ==========================================

from django import forms
from django.core.exceptions import ValidationError

from .models import ReportCategory


class ReportCategoryForm(forms.ModelForm):

    class Meta:
        model = ReportCategory
        fields = ["name", "priority"]

    # --------------------------------------
    # FIELD-LEVEL VALIDATION
    # --------------------------------------

    def clean_name(self):

        name = self.cleaned_data["name"].strip()

        if name.lower() == "unknown":
            raise ValidationError(
                "Please enter a descriptive category name."
            )

        return name

    # --------------------------------------
    # FORM-LEVEL VALIDATION
    # --------------------------------------

    def clean(self):

        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        priority = cleaned_data.get("priority")

        if (
            name
            and name.lower() == "featured"
            and priority is not None
            and priority < 5
        ):
            self.add_error(
                "priority",
                "Featured categories require priority 5 or higher."
            )

        return cleaned_data
