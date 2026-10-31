
# ================================================
# DAY 216 - REPORT CATEGORY CREATE VIEW
# ================================================

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .mixins import StaffOnlyMixin
from .models import ReportCategory
from .report_category_forms import ReportCategoryForm


class ReportCategoryCreateView(StaffOnlyMixin, CreateView):

    model = ReportCategory

    form_class = ReportCategoryForm

    template_name = "homepage/report_category_form.html"

    success_url = reverse_lazy("report_category_create")

    def form_valid(self, form):

        messages.success(
            self.request,
            "Report category created successfully!"
        )

        return super().form_valid(form)
