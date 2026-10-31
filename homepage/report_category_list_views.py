
"""Report category dashboard: filtering, analytics, saved filters, and history."""

from urllib.parse import urlencode

from django.db.models import Avg, Count, Q
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView

from .mixins import StaffOnlyMixin
from .models import ReportCategory


class ReportCategoryListView(StaffOnlyMixin, ListView):
    model = ReportCategory
    template_name = "homepage/report_category_list.html"
    context_object_name = "categories"
    paginate_by = 10

    SAVED_FILTERS_SESSION_KEY = "report_category_saved_filters"
    RECENT_FILTER_HISTORY_SESSION_KEY = "report_category_recent_filter_history"
    MAX_RECENT_FILTERS = 5

    SORT_OPTIONS = {
        "name_asc": ("name", "pk"),
        "name_desc": ("-name", "-pk"),
        "priority_high": ("-priority", "name", "pk"),
        "priority_low": ("priority", "name", "pk"),
    }

    # DAY 220: Sorting and priority validation
    def get_sort_order(self):
        sort = self.request.GET.get("sort", "name_asc")
        return sort if sort in self.SORT_OPTIONS else "name_asc"

    def get_priority_filter(self):
        priority = self.request.GET.get("priority", "all")
        return priority if priority in {"all", "high", "low"} else "all"

    # DAY 225: Optional numeric priority bounds
    def parse_priority_bound(self, parameter_name):
        raw_value = self.request.GET.get(parameter_name, "").strip()
        if not raw_value:
            return None
        try:
            return int(raw_value)
        except ValueError:
            return None

    def apply_priority_range(self, queryset):
        minimum = self.parse_priority_bound("min_priority")
        maximum = self.parse_priority_bound("max_priority")

        if minimum is not None:
            queryset = queryset.filter(priority__gte=minimum)
        if maximum is not None:
            queryset = queryset.filter(priority__lte=maximum)
        return queryset

    # DAY 226: Range validation and display
    def get_range_validation_messages(self):
        messages = []
        raw_minimum = self.request.GET.get("min_priority", "").strip()
        raw_maximum = self.request.GET.get("max_priority", "").strip()
        minimum = self.parse_priority_bound("min_priority")
        maximum = self.parse_priority_bound("max_priority")

        if raw_minimum and minimum is None:
            messages.append("Minimum priority must be a valid whole number.")
        if raw_maximum and maximum is None:
            messages.append("Maximum priority must be a valid whole number.")
        if minimum is not None and maximum is not None and minimum > maximum:
            messages.append(
                "Minimum priority cannot be greater than maximum priority."
            )
        return messages

    def get_active_range_summary(self):
        minimum = self.parse_priority_bound("min_priority")
        maximum = self.parse_priority_bound("max_priority")

        if minimum is None and maximum is None:
            return ""
        if minimum is not None and maximum is not None:
            return f"Priority range: {minimum} to {maximum}"
        if minimum is not None:
            return f"Minimum priority: {minimum}"
        return f"Maximum priority: {maximum}"

    # DAYS 219-220, 225: Search, priority filtering, and sorting
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.apply_priority_range(queryset)
        query = self.request.GET.get("q", "").strip()
        priority_filter = self.get_priority_filter()
        sort_order = self.get_sort_order()

        if query:
            queryset = queryset.filter(Q(name__icontains=query))
        if priority_filter == "high":
            queryset = queryset.filter(priority__gte=5)
        elif priority_filter == "low":
            queryset = queryset.filter(priority__lt=5)

        return queryset.order_by(*self.SORT_OPTIONS[sort_order])

    # DAYS 221-222: Category statistics and percentages
    def get_category_statistics(self):
        statistics = ReportCategory.objects.aggregate(
            total=Count("pk"),
            high=Count("pk", filter=Q(priority__gte=5)),
            low=Count("pk", filter=Q(priority__lt=5)),
            average=Avg("priority"),
        )
        statistics["average"] = round(statistics["average"] or 0.0, 2)
        total = statistics["total"]

        if total > 0:
            statistics["high_percentage"] = round(
                statistics["high"] / total * 100, 2
            )
            statistics["low_percentage"] = round(
                statistics["low"] / total * 100, 2
            )
        else:
            statistics["high_percentage"] = 0.0
            statistics["low_percentage"] = 0.0
        return statistics

    # DAY 223: Highest/lowest category insights
    def get_category_insights(self):
        highest = (
            ReportCategory.objects.order_by("-priority", "name", "pk")
            .values("name", "priority")
            .first()
        )
        lowest = (
            ReportCategory.objects.order_by("priority", "name", "pk")
            .values("name", "priority")
            .first()
        )
        if highest is None or lowest is None:
            return {"highest": None, "lowest": None, "spread": 0}
        return {
            "highest": highest,
            "lowest": lowest,
            "spread": highest["priority"] - lowest["priority"],
        }

    # DAY 224: Five highest-priority categories
    def get_top_priority_report(self):
        top_categories = list(
            ReportCategory.objects.order_by("-priority", "name", "pk")
            .values("name", "priority")[:5]
        )
        if not top_categories:
            return []

        max_priority = top_categories[0]["priority"]
        report = []
        for category in top_categories:
            priority = category["priority"]
            percentage = (
                round(priority / max_priority * 100, 2)
                if max_priority > 0
                else 0.0
            )
            percentage = max(0.0, min(100.0, percentage))
            report.append(
                {
                    "name": category["name"],
                    "priority": priority,
                    "percentage": percentage,
                }
            )
        return report

    # DAY 227: Quick filter presets
    def get_filter_presets(self):
        search_query = self.request.GET.get("q", "").strip()
        base_url = reverse("report_category_list")
        definitions = [
            {"key": "all", "label": "All Categories", "priority": "all",
             "sort": "name_asc", "minimum": None, "maximum": None},
            {"key": "high", "label": "High Priority", "priority": "high",
             "sort": "priority_high", "minimum": None, "maximum": None},
            {"key": "low", "label": "Low Priority", "priority": "low",
             "sort": "priority_low", "minimum": None, "maximum": None},
            {"key": "range", "label": "Priority 4-8", "priority": "all",
             "sort": "priority_high", "minimum": 4, "maximum": 8},
        ]
        current_priority = self.get_priority_filter()
        current_sort = self.get_sort_order()
        current_minimum = self.parse_priority_bound("min_priority")
        current_maximum = self.parse_priority_bound("max_priority")
        presets = []

        for definition in definitions:
            parameters = {
                "priority": definition["priority"],
                "sort": definition["sort"],
            }
            if search_query:
                parameters["q"] = search_query
            if definition["minimum"] is not None:
                parameters["min_priority"] = definition["minimum"]
            if definition["maximum"] is not None:
                parameters["max_priority"] = definition["maximum"]

            is_active = (
                current_priority == definition["priority"]
                and current_sort == definition["sort"]
                and current_minimum == definition["minimum"]
                and current_maximum == definition["maximum"]
            )
            presets.append(
                {
                    "key": definition["key"],
                    "label": definition["label"],
                    "url": base_url + "?" + urlencode(parameters),
                    "active": is_active,
                }
            )
        return presets

    # DAY 228: Validate and save filter preferences
    def normalize_filter_data(self, data):
        priority = data.get("priority", "all")
        if priority not in {"all", "high", "low"}:
            priority = "all"
        sort = data.get("sort", "name_asc")
        if sort not in self.SORT_OPTIONS:
            sort = "name_asc"

        filters = {
            "q": str(data.get("q", "")).strip(),
            "priority": priority,
            "sort": sort,
        }
        for field in ("min_priority", "max_priority"):
            raw_value = str(data.get(field, "")).strip()
            if not raw_value:
                continue
            try:
                filters[field] = str(int(raw_value))
            except ValueError:
                continue
        return filters

    def build_filter_url(self, filters):
        base_url = reverse("report_category_list")
        query_string = urlencode(filters)
        return f"{base_url}?{query_string}"

    # DAY 229: Identify meaningful filter combinations
    def has_meaningful_filters(self, filters):
        return any(
            (
                bool(filters.get("q", "")),
                filters.get("priority", "all") != "all",
                filters.get("sort", "name_asc") != "name_asc",
                "min_priority" in filters,
                "max_priority" in filters,
            )
        )

    def record_recent_filter_history(self):
        current_filters = self.normalize_filter_data(self.request.GET)
        if not self.has_meaningful_filters(current_filters):
            return

        history = self.request.session.get(
            self.RECENT_FILTER_HISTORY_SESSION_KEY, []
        )
        if not isinstance(history, list):
            history = []

        # Move the current combination to the front without duplicates.
        history = [
            item for item in history
            if isinstance(item, dict) and item != current_filters
        ]
        history.insert(0, current_filters)
        self.request.session[self.RECENT_FILTER_HISTORY_SESSION_KEY] = (
            history[:self.MAX_RECENT_FILTERS]
        )

    def describe_filter_history_entry(self, filters):
        parts = []
        search_query = filters.get("q", "")
        if search_query:
            parts.append(f"Search: {search_query}")
        priority = filters.get("priority", "all")
        if priority != "all":
            parts.append(f"Priority: {priority.title()}")
        sort = filters.get("sort", "name_asc")
        if sort != "name_asc":
            parts.append(f"Sort: {sort.replace('_', ' ').title()}")
        if "min_priority" in filters:
            parts.append(f"Min: {filters['min_priority']}")
        if "max_priority" in filters:
            parts.append(f"Max: {filters['max_priority']}")
        return " · ".join(parts) or "All Categories"


    # ==========================================
    # DAY 232 - SAFE HISTORY SEARCH INPUT
    # ==========================================

    def get_history_search_query(self):
        """
        Return a cleaned history search keyword.

        - Remove surrounding whitespace.
        - Limit the keyword to 100 characters.
        """

        query = self.request.GET.get(
            "history_q",
            "",
        )

        return query.strip()[:100]

    # DAY 230: Only ONE definition of this method must exist.

    # ==========================================
    # DAY 231 - SEARCHABLE FILTER HISTORY
    # ==========================================

    def get_recent_filter_history(self, search_query=None):
        """
        Return history entries with their original
        session indexes.

        Optionally filter entries by a
        case-insensitive search keyword.
        """

        stored_history = self.request.session.get(
            self.RECENT_FILTER_HISTORY_SESSION_KEY,
            [],
        )

        if not isinstance(stored_history, list):
            return []

        # None means: use the current URL search.
        # An empty string means: show all entries.
        if search_query is None:
            search_query = self.get_history_search_query()

        search_query = search_query.strip().casefold()

        recent_history = []

        for index, item in enumerate(
            stored_history[:self.MAX_RECENT_FILTERS]
        ):

            # Ignore invalid session entries.
            if not isinstance(item, dict):
                continue

            filters = self.normalize_filter_data(item)

            # Ignore default or meaningless filters.
            if not self.has_meaningful_filters(filters):
                continue

            label = self.describe_filter_history_entry(
                filters
            )

            # DAY 231: Only display matching entries.
            if search_query:
                if search_query not in label.casefold():
                    continue

            recent_history.append(
                {
                    # Keep the ORIGINAL session index.
                    "index": index,

                    "label": label,

                    "url": self.build_filter_url(
                        filters
                    ),
                }
            )

        return recent_history


    # ==========================================
    # DAY 230 + 231 - REMOVE HISTORY ENTRY
    # ==========================================
    def remove_recent_filter_history_entry(self, raw_index):
        """
        Remove one history entry using its original
        session index.

        Returns:
            True  - Entry successfully removed.
            False - Invalid or missing index.
        """
        history = self.request.session.get(
            self.RECENT_FILTER_HISTORY_SESSION_KEY,
            [],
        )
        if not isinstance(history, list):
            return False

        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            return False

        if index < 0 or index >= len(history):
            return False

        updated_history = history.copy()
        updated_history.pop(index)
        self.request.session[
            self.RECENT_FILTER_HISTORY_SESSION_KEY
        ] = updated_history
        return True

    # DAYS 228-230: Handle state changes with POST.
    def post(self, request, *args, **kwargs):
        action = request.POST.get("saved_filter_action")

        if action == "remove_history_entry":
            removed = self.remove_recent_filter_history_entry(
                request.POST.get("history_index")
            )
            if not removed:
                return HttpResponseBadRequest("Invalid history entry index.")
            return HttpResponseRedirect(reverse("report_category_list"))

        if action == "clear_history":
            request.session.pop(self.RECENT_FILTER_HISTORY_SESSION_KEY, None)
            return HttpResponseRedirect(reverse("report_category_list"))

        if action not in {"save", "clear"}:
            return HttpResponseBadRequest("Invalid saved filter action.")

        current_filters = self.normalize_filter_data(request.POST)
        if action == "save":
            request.session[self.SAVED_FILTERS_SESSION_KEY] = current_filters
        else:
            request.session.pop(self.SAVED_FILTERS_SESSION_KEY, None)
        return HttpResponseRedirect(self.build_filter_url(current_filters))

    # ==========================================
    # DAY 232 - HISTORY SEARCH FEEDBACK
    # ==========================================
    def get_history_search_feedback(
        self,
        search_query,
        visible_count,
        total_count,
    ):
        """
        Return a helpful message describing
        the current history search results.
        """
        if total_count == 0:
            return "No recent filter history yet."

        if search_query:
            if visible_count == 0:
                return (
                    f'No history entries match '
                    f'"{search_query}".'
                )

            return (
                f"Showing {visible_count} of "
                f"{total_count} history entries "
                f'for "{search_query}".'
            )

        if total_count == 1:
            return "1 recent history entry available."

        return (
            f"{total_count} recent history "
            f"entries available."
        )

    # DAYS 221-230: Context for the existing dashboard template.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["priority_filter"] = self.get_priority_filter()
        context["sort_order"] = self.get_sort_order()
        context["category_stats"] = self.get_category_statistics()
        context["category_insights"] = self.get_category_insights()
        context["top_priority_report"] = self.get_top_priority_report()

        minimum = self.parse_priority_bound("min_priority")
        maximum = self.parse_priority_bound("max_priority")
        context["min_priority"] = "" if minimum is None else minimum
        context["max_priority"] = "" if maximum is None else maximum
        context["range_messages"] = self.get_range_validation_messages()
        context["active_range_summary"] = self.get_active_range_summary()
        context["filter_presets"] = self.get_filter_presets()

        saved_filters = self.request.session.get(self.SAVED_FILTERS_SESSION_KEY)
        if isinstance(saved_filters, dict):
            saved_filters = self.normalize_filter_data(saved_filters)
        else:
            saved_filters = None
        context["saved_category_filters"] = saved_filters
        context["current_category_filters"] = self.normalize_filter_data(
            self.request.GET
        )
        context["saved_category_filters_url"] = (
            self.build_filter_url(saved_filters)
            if saved_filters is not None
            else ""
        )


        # ======================================
        # DAY 231 - SEARCHABLE HISTORY CONTEXT
        # ======================================

        self.record_recent_filter_history()

        # Read the keyword from the URL.
        history_search_query = (
            self.get_history_search_query()
        )

        # Entries matching the search.
        recent_history = (
            self.get_recent_filter_history()
        )

        # All valid history entries, without search.
        all_history = (
            self.get_recent_filter_history(
                search_query=""
            )
        )

        context["history_search_query"] = (
            history_search_query
        )

        context["recent_filter_history"] = (
            recent_history
        )

        context["recent_history_total_count"] = (
            len(all_history)
        )


        context["recent_history_visible_count"] = (
            len(recent_history)
        )

        # ======================================
        # DAY 232 - SEARCH UX CONTEXT
        # ======================================

        context["history_search_active"] = bool(
            history_search_query
        )

        context["history_search_feedback"] = (
            self.get_history_search_feedback(
                search_query=history_search_query,
                visible_count=len(recent_history),
                total_count=len(all_history),
            )
        )

        return context
