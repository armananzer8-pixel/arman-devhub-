
# ==========================================
# DAY 217 - UPDATE AND DELETE CATEGORY VIEWS
# ==========================================

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView

from .mixins import StaffOnlyMixin
from .models import ReportCategory
from .report_category_forms import ReportCategoryForm


# ------------------------------------------
# UPDATE AN EXISTING REPORT CATEGORY
# ------------------------------------------

class ReportCategoryUpdateView(StaffOnlyMixin, UpdateView):

    model = ReportCategory

    form_class = ReportCategoryForm

    template_name = "homepage/report_category_update.html"

    success_url = reverse_lazy("report_category_create")

    def form_valid(self, form):

        messages.success(
            self.request,
            "Report category updated successfully!"
        )

        return super().form_valid(form)


# ------------------------------------------
# DELETE AN EXISTING REPORT CATEGORY
# ------------------------------------------

class ReportCategoryDeleteView(StaffOnlyMixin, DeleteView):

    model = ReportCategory

    template_name = (
        "homepage/report_category_confirm_delete.html"
    )

    success_url = reverse_lazy("report_category_create")

    def form_valid(self, form):

        messages.success(
            self.request,
            "Report category deleted successfully!"
        )

        return super().form_valid(form)
