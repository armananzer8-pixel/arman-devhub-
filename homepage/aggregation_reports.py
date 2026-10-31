
# =====================================================
# DAY 209 - ADVANCED ATTACHMENT REPORTING
# Arman DevHub
# =====================================================

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from .mixins import StaffOnlyMixin
from .models import ContactMessage


class AttachmentSummaryReportView(
    StaffOnlyMixin,
    TemplateView,
):
    """
    Staff-only attachment summary report.

    Features:
    - Date filtering
    - Sorting
    - Database aggregation
    - Top 10 contact messages
    """

    template_name = "homepage/attachment_summary.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # ---------------------------------------------
        # 1. READ DATE FILTER
        # ---------------------------------------------

        date_range = self.request.GET.get(
            "date_range", "all"
        )

        allowed_ranges = {"all", "7", "30", "90"}

        if date_range not in allowed_ranges:
            date_range = "all"

        # ---------------------------------------------
        # 2. READ SORT OPTION
        # ---------------------------------------------

        sort = self.request.GET.get(
            "sort", "most"
        )

        allowed_sorts = {
            "most": ("-attachment_count", "-pk"),
            "least": ("attachment_count", "pk"),
            "name": ("name", "pk"),
        }

        if sort not in allowed_sorts:
            sort = "most"

        # ---------------------------------------------
        # 3. CREATE DATE CONDITION
        # ---------------------------------------------

        if date_range == "all":

            attachment_count = Count("attachments")

        else:

            days = int(date_range)

            cutoff = timezone.now() - timedelta(
                days=days
            )

            attachment_count = Count(
                "attachments",
                filter=Q(
                    attachments__uploaded_at__gte=cutoff
                ),
            )

        # ---------------------------------------------
        # 4. ANNOTATE ATTACHMENT COUNTS
        # ---------------------------------------------

        message_queryset = (
            ContactMessage.objects
            .annotate(
                attachment_count=attachment_count
            )
            .order_by()
        )

        # ---------------------------------------------
        # 5. CALCULATE SUMMARY STATISTICS
        # ---------------------------------------------

        statistics = message_queryset.aggregate(
            total_messages=Count("pk"),
            total_attachments=Sum("attachment_count"),
            average_attachments=Avg("attachment_count"),
        )

        context["summary"] = {
            "total_messages": (
                statistics["total_messages"] or 0
            ),
            "total_attachments": (
                statistics["total_attachments"] or 0
            ),
            "average_attachments": (
                statistics["average_attachments"] or 0
            ),
        }

        # ---------------------------------------------
        # 6. SORT AND LIMIT RESULTS
        # ---------------------------------------------

        ordering = allowed_sorts[sort]

        top_messages = (
            message_queryset
            .order_by(*ordering)[:10]
        )

        # ---------------------------------------------
        # 7. TEMPLATE CONTEXT
        # ---------------------------------------------

        context["message_counts"] = top_messages

        context["selected_date_range"] = date_range

        context["selected_sort"] = sort

        context["page_title"] = (
            "Attachment Summary Report"
        )

        return context
