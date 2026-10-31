from django.views.generic import ListView
from .models import MessageAttachment

import csv

from datetime import timedelta

from pathlib import Path

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    ContactForm,
    DeveloperProfileForm,
    MessageAttachmentForm,
    MessageAttachmentReplaceForm,
    MessageNoteForm,
    ProfileForm,
    SignupForm,
    StaffContactMessageForm,
)
from .mixins import StaffOnlyMixin
from .models import (
    ContactMessage,
    DeveloperProfile,
    MessageAttachment,
    MessageNote,
    MessageTag,
)


def home(request):
    return render(request, "homepage/home.html")


def about(request):
    return render(request, "homepage/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                message=form.cleaned_data["message"],
            )
            return render(
                request,
                "homepage/contact.html",
                {
                    "form": ContactForm(),
                    "success_message": "Your message has been sent successfully.",
                },
            )
    else:
        form = ContactForm()

    return render(request, "homepage/contact.html", {"form": form})


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created. You can now log in.")
            return redirect("login")
    else:
        form = SignupForm()

    return render(request, "homepage/signup.html", {"form": form})


@staff_member_required
def message_list(request):
    query = request.GET.get("q", "").strip()
    search_field = request.GET.get("field", "all")
    sort_by = request.GET.get("sort", "newest")
    extension = request.GET.get("extension", "").strip()

    messages_queryset = ContactMessage.objects.all()
    if query:
        if search_field == "name":
            messages_queryset = messages_queryset.filter(name__icontains=query)
        elif search_field == "email":
            messages_queryset = messages_queryset.filter(email__icontains=query)
        elif search_field == "message":
            messages_queryset = messages_queryset.filter(message__icontains=query)
        else:
            messages_queryset = messages_queryset.filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(message__icontains=query)
            )

    if sort_by == "oldest":
        messages_queryset = messages_queryset.order_by("created_at", "id")
    elif sort_by in {"name", "name_asc"}:
        sort_by = "name_asc"
        messages_queryset = messages_queryset.order_by("name", "created_at", "id")
    elif sort_by == "name_desc":
        messages_queryset = messages_queryset.order_by("-name", "-created_at", "-id")
    else:
        sort_by = "newest"
        messages_queryset = messages_queryset.order_by("-created_at", "-id")

    paginator = Paginator(messages_queryset, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

    attachments = MessageAttachment.objects.select_related("contact_message").all()
    if query:
        attachments = attachments.filter(
            Q(file__icontains=query)
            | Q(contact_message__name__icontains=query)
            | Q(contact_message__email__icontains=query)
        )
    if extension:
        if not extension.startswith("."):
            extension = f".{extension}"
        attachments = attachments.filter(file__iendswith=extension)

    # Day 234 - Optimized attachment sorting and pagination
    if sort_by == "oldest":
        attachment_source = attachments.order_by("uploaded_at", "pk")

    elif sort_by in {"filename", "filename_desc", "size_asc", "size_desc"}:
        attachment_source = list(attachments)

        if sort_by == "filename":
            attachment_source.sort(
                key=lambda item: item.file.name.casefold()
            )
        elif sort_by == "filename_desc":
            attachment_source.sort(
                key=lambda item: item.file.name.casefold(),
                reverse=True
            )
        elif sort_by == "size_asc":
            attachment_source.sort(
                key=lambda item: item.file.size
            )
        else:
            attachment_source.sort(
                key=lambda item: item.file.size,
                reverse=True
            )

    else:
        attachment_source = attachments.order_by(
            "-uploaded_at", "-pk"
        )

    attachment_paginator = Paginator(attachment_source, 10)
    attachment_page = attachment_paginator.get_page(
        request.GET.get("page")
    )
    page_attachments = list(attachment_page.object_list)
    attachment_metadata = [
        {
            "attachment": attachment,
            "filename": Path(attachment.file.name).name,
            "extension": Path(attachment.file.name).suffix.lower(),
            "size_bytes": attachment.file.size,
        }
        for attachment in page_attachments
    ]

    all_attachments = MessageAttachment.objects.all()
    attachment_statistics = all_attachments.aggregate(
        total_attachments=Count("id"),
        total_messages=Count("contact_message", distinct=True),
    )

    file_type_counts = {}
    for ext in [".pdf", ".txt", ".jpg", ".jpeg", ".png", ".gif", ".doc", ".docx"]:
        file_type_counts[ext] = all_attachments.filter(file__iendswith=ext).count()

    known_count = sum(file_type_counts.values())
    statistics = {
        "total_messages": ContactMessage.objects.count(),
        "total_notes": MessageNote.objects.count(),
        "used_tags": MessageTag.objects.filter(
            contact_messages__isnull=False
        ).distinct().count(),
    }
    popular_tags = (
        MessageTag.objects.annotate(
            message_count=Count("contact_messages", distinct=True)
        )
        .filter(message_count__gt=0)
        .order_by("-message_count", "name")[:5]
    )
    context = {
        "messages": page_obj.object_list,
        "attachments": page_attachments,
        "attachment_metadata": attachment_metadata,
        "total_messages": messages_queryset.count(),
        "total_attachments": attachment_statistics["total_attachments"],
        "search_query": query,
        "search_field": search_field,
        "selected_extension": extension,
        "selected_sort": sort_by,
        "sort_by": sort_by,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "attachment_page_obj": attachment_page,
        "attachment_paginator": attachment_paginator,
        "allowed_extensions": [".pdf", ".txt", ".jpg", ".jpeg", ".png", ".gif", ".doc", ".docx"],
        "statistics": statistics,
        "popular_tags": popular_tags,
        "analytics": {
            "total_attachments": attachment_statistics["total_attachments"],
            "messages_with_attachments": attachment_statistics["total_messages"],
            "file_type_counts": file_type_counts,
            "other_files": max(
                0,
                attachment_statistics["total_attachments"] - known_count,
            ),
            "pdf_count": file_type_counts[".pdf"],
            "txt_count": file_type_counts[".txt"],
            "image_count": sum(file_type_counts[ext] for ext in (".jpg", ".jpeg", ".png")),
        },
        "file_type_statistics": [
            {"extension": ext, "count": count}
            for ext, count in file_type_counts.items()
        ],
    }
    return render(request, "homepage/message_list.html", context)


@login_required
def profile(request):
    developer_profile, _ = DeveloperProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        developer_form = DeveloperProfileForm(
            request.POST,
            instance=developer_profile,
        )
        profile_is_valid = form.is_valid()
        developer_profile_is_valid = developer_form.is_valid()
        if profile_is_valid and developer_profile_is_valid:
            form.save()
            developer_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
        developer_form = DeveloperProfileForm(instance=developer_profile)

    return render(
        request,
        "homepage/profile.html",
        {
            "form": form,
            "developer_form": developer_form,
        },
    )


class LearningHubView(TemplateView):
    template_name = "homepage/learning_hub.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_heading": "Backend Learning Hub",
                "topics": [
                    {
                        "name": "Python",
                        "description": "Build a strong foundation in Python.",
                    },
                    {
                        "name": "Django",
                        "description": "Create web applications with Django.",
                    },
                    {
                        "name": "Databases",
                        "description": "Model and query application data.",
                    },
                ],
            }
        )
        return context


class ContactMessageListView(StaffOnlyMixin, ListView):
    model = ContactMessage
    template_name = "homepage/message_browse.html"
    context_object_name = "contact_messages"
    paginate_by = 5
    ordering = ("-created_at", "-pk")


class ContactMessageDetailView(StaffOnlyMixin, DetailView):
    model = ContactMessage
    template_name = "homepage/message_detail.html"
    context_object_name = "contact_message"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("tags", "notes", "attachments")
        )


class ContactMessageCreateView(
    StaffOnlyMixin,
    SuccessMessageMixin,
    CreateView,
):
    model = ContactMessage
    form_class = StaffContactMessageForm
    template_name = "homepage/message_form.html"
    success_message = "Contact message for %(name)s created successfully."

    def get_success_url(self):
        return reverse("message_detail", kwargs={"pk": self.object.pk})


class ContactMessageUpdateView(
    StaffOnlyMixin,
    SuccessMessageMixin,
    UpdateView,
):
    model = ContactMessage
    form_class = StaffContactMessageForm
    template_name = "homepage/message_form.html"
    success_message = "Contact message for %(name)s updated successfully."

    def get_success_url(self):
        return reverse("message_detail", kwargs={"pk": self.object.pk})


class ContactMessageDeleteView(StaffOnlyMixin, DeleteView):
    model = ContactMessage
    template_name = "homepage/message_confirm_delete.html"
    context_object_name = "contact_message"
    success_url = reverse_lazy("message_browse")


class MessageNoteFormView(StaffOnlyMixin, FormView):
    form_class = MessageNoteForm
    template_name = "homepage/message_note_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.contact_message = get_object_or_404(
            ContactMessage,
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_message"] = self.contact_message
        return context

    def form_valid(self, form):
        MessageNote.objects.create(
            contact_message=self.contact_message,
            note=form.cleaned_data["note"],
        )
        messages.success(self.request, "Note added successfully.")
        return redirect(
            "message_detail",
            pk=self.contact_message.pk,
        )


class MessageAttachmentCreateView(StaffOnlyMixin, FormView):
    form_class = MessageAttachmentForm
    template_name = "homepage/message_attachment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.contact_message = get_object_or_404(
            ContactMessage,
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_message"] = self.contact_message
        return context

    def form_valid(self, form):
        attachment = form.save(commit=False)
        attachment.contact_message = self.contact_message
        attachment.save()
        messages.success(self.request, "Attachment uploaded successfully.")
        return redirect(
            "message_detail",
            pk=self.contact_message.pk,
        )


@staff_member_required
def download_message_attachment(_request, attachment_id):
    attachment = get_object_or_404(MessageAttachment, pk=attachment_id)
    return FileResponse(
        attachment.file.open("rb"),
        as_attachment=True,
        filename=Path(attachment.file.name).name,
    )


class MessageAttachmentDeleteView(StaffOnlyMixin, DeleteView):
    model = MessageAttachment
    template_name = "homepage/message_attachment_confirm_delete.html"
    context_object_name = "attachment"
    http_method_names = ["get", "post", "head", "options"]

    def get_success_url(self):
        return reverse(
            "message_detail",
            kwargs={"pk": self.object.contact_message_id},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Attachment deleted successfully.")
        return response


class MessageAttachmentReplaceView(
    StaffOnlyMixin,
    SuccessMessageMixin,
    UpdateView,
):
    model = MessageAttachment
    form_class = MessageAttachmentReplaceForm
    template_name = "homepage/message_attachment_replace.html"
    context_object_name = "attachment"
    success_message = "Attachment replaced successfully."

    def get_success_url(self):
        return reverse(
            "message_detail",
            kwargs={"pk": self.object.contact_message_id},
        )

    def form_valid(self, form):
        old_name = MessageAttachment.objects.values_list(
            "file",
            flat=True,
        ).get(pk=self.object.pk)
        old_storage = self.object.file.storage
        response = super().form_valid(form)

        if old_name != self.object.file.name:
            attachment_id = self.object.pk

            def delete_old_file():
                still_in_use = MessageAttachment.objects.filter(
                    file=old_name
                ).exclude(pk=attachment_id).exists()
                if not still_in_use:
                    old_storage.delete(old_name)

            transaction.on_commit(delete_old_file)

        return response



class AttachmentDashboardView(StaffOnlyMixin, TemplateView):
    template_name = "homepage/attachment_dashboard.html"

    ALLOWED_EXTENSIONS = (
        ".pdf",
        ".txt",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".doc",
        ".docx",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request = self.request

                # DAY 197 - DATE RANGE FILTER
        date_range = request.GET.get(
            "date_range", "all"
        ).strip().lower()

        allowed_date_ranges = {"all", "7", "30", "90"}

        if date_range not in allowed_date_ranges:
            date_range = "all"

        # ======================================
        # DAY 193 - SEARCH AND FILTERING
        # ======================================

        query = request.GET.get("q", "").strip()
        extension = request.GET.get(
            "extension", ""
        ).strip().lower()
        sort_by = request.GET.get("sort", "newest")

        attachments = MessageAttachment.objects.select_related(
            "contact_message"
        )

        if query:
            attachments = attachments.filter(
                Q(file__icontains=query)
                | Q(contact_message__name__icontains=query)
                | Q(contact_message__email__icontains=query)
            )

        if extension:
            if not extension.startswith("."):
                extension = f".{extension}"

            attachments = attachments.filter(
                file__iendswith=extension
            )

        # Day 234 - Optimized dashboard pagination
        if sort_by == "oldest":
            attachment_source = attachments.order_by(
                "uploaded_at", "pk"
            )

        elif sort_by in {
            "filename",
            "filename_desc",
            "size_asc",
            "size_desc",
        }:
            attachment_source = list(attachments)

            if sort_by == "filename":
                attachment_source.sort(
                    key=lambda item: item.file.name.casefold()
                )
            elif sort_by == "filename_desc":
                attachment_source.sort(
                    key=lambda item: item.file.name.casefold(),
                    reverse=True
                )
            elif sort_by == "size_asc":
                attachment_source.sort(
                    key=lambda item: item.file.size
                )
            else:
                attachment_source.sort(
                    key=lambda item: item.file.size,
                    reverse=True
                )

        else:
            sort_by = "newest"
            attachment_source = attachments.order_by(
                "-uploaded_at", "-pk"
            )

        paginator = Paginator(attachment_source, 10)

        page_obj = paginator.get_page(
            request.GET.get("page")
        )

        page_attachments = list(
            page_obj.object_list
        )

        # ======================================
        # DAY 193 - ATTACHMENT METADATA
        # ======================================

        attachment_metadata = []

        for attachment in page_attachments:
            filename = Path(attachment.file.name).name
            extension_name = Path(filename).suffix.lower()

            try:
                size_bytes = attachment.file.size
            except (OSError, ValueError, NotImplementedError):
                size_bytes = None

            attachment_metadata.append({
                "attachment": attachment,
                "filename": filename,
                "extension": extension_name,
                "size_bytes": size_bytes,
            })

        # ======================================
        # DAY 196 - CHART TYPE FILTER
        # ======================================

        chart_type = request.GET.get(
            "chart_type", "all"
        ).strip().lower()

        allowed_chart_types = {
            "all",
            "pdf",
            "txt",
            "images",
            "gif",
            "word",
            "other",
        }

        if chart_type not in allowed_chart_types:
            chart_type = "all"

        # ======================================
        # DAY 194 - DATABASE ANALYTICS
        # ======================================

        # Use ALL attachments so dashboard
        # analytics are independent of filters.

        all_attachments = MessageAttachment.objects.all()

        # DAY 197 - FILTERED ANALYTICS QUERYSET
        chart_attachments = all_attachments

        if date_range != "all":
            cutoff_date = timezone.now() - timedelta(
                days=int(date_range)
            )

            chart_attachments = chart_attachments.filter(
                uploaded_at__gte=cutoff_date
            )

        statistics = all_attachments.aggregate(
            total_attachments=Count("pk"),
            total_messages=Count(
                "contact_message",
                distinct=True,
            ),
        )

        # Count attachments by extension.
        file_type_counts = {
            ext: all_attachments.filter(
                file__iendswith=ext
            ).count()
            for ext in self.ALLOWED_EXTENSIONS
        }

        known_count = sum(
            file_type_counts.values()
        )

        # ======================================
        # DAY 194 - SUMMARY CARD VALUES
        # ======================================

        pdf_count = file_type_counts.get(
            ".pdf", 0
        )

        txt_count = file_type_counts.get(
            ".txt", 0
        )

        image_count = sum(
            file_type_counts.get(ext, 0)
            for ext in (
                ".jpg",
                ".jpeg",
                ".png",
            )
        )

        other_files = max(
            0,
            statistics["total_attachments"] - known_count,
        )

        # ======================================
        # DAY 193 - PRESERVE FILTERS IN LINKS
        # ======================================

        filter_parameters = request.GET.copy()
        filter_parameters.pop("page", None)

        # ======================================
        # DAY 196 - FILTERED CHART DATA
        # ======================================

        # DAY 197 - COUNTS FOR SELECTED DATE RANGE
        date_file_counts = {
            ext: chart_attachments.filter(
                file__iendswith=ext
            ).count()
            for ext in self.ALLOWED_EXTENSIONS
        }

        date_total = chart_attachments.count()

        date_pdf_count = date_file_counts.get(".pdf", 0)
        date_txt_count = date_file_counts.get(".txt", 0)

        date_image_count = sum(
            date_file_counts.get(ext, 0)
            for ext in (".jpg", ".jpeg", ".png")
        )

        date_word_count = (
            date_file_counts.get(".doc", 0)
            + date_file_counts.get(".docx", 0)
        )

        date_other_count = max(
            0,
            date_total - sum(date_file_counts.values()),
        )

        chart_categories = [
            ("pdf", "PDF", date_pdf_count),
            ("txt", "TXT", date_txt_count),
            ("images", "Images", date_image_count),
            ("gif", "GIF", date_file_counts.get(".gif", 0)),
            ("word", "Word Documents", date_word_count),
            ("other", "Other", date_other_count),
        ]

        if chart_type == "all":
            selected_categories = chart_categories
        else:
            selected_categories = [
                category
                for category in chart_categories
                if category[0] == chart_type
            ]

        chart_labels = [
            label
            for _, label, _ in selected_categories
        ]

        chart_counts = [
            count
            for _, _, count in selected_categories
        ]

        # ======================================
        # FINAL TEMPLATE CONTEXT
        # ======================================

        context.update(
            {
                "attachments": page_attachments,

                "attachment_metadata": (
                    attachment_metadata
                ),

                "total_attachments": (
                    len(page_attachments)
                    if not isinstance(page_obj, Paginator)
                    else page_obj.paginator.count
                ),

                "search_query": query,
                "selected_extension": extension,
                "selected_sort": sort_by,
                "sort_by": sort_by,

                "allowed_extensions": (
                    self.ALLOWED_EXTENSIONS
                ),

                "page_obj": page_obj,
                "paginator": paginator,

                "is_paginated": (
                    page_obj.has_other_pages()
                ),

                "filter_query_string": (
                    filter_parameters.urlencode()
                ),

                # DAY 194 ANALYTICS

                "analytics": {
                    "total_attachments": (
                        statistics["total_attachments"]
                    ),

                    "messages_with_attachments": (
                        statistics["total_messages"]
                    ),

                    "file_type_counts": (
                        file_type_counts
                    ),

                    "other_files": other_files,

                    "pdf_count": pdf_count,

                    "txt_count": txt_count,

                    "image_count": image_count,
                },

                "selected_chart_type": chart_type,

                "selected_date_range": date_range,

                "attachment_chart_data": {
                    "labels": chart_labels,
                    "counts": chart_counts,
                },
                "file_type_statistics": [
                    {
                        "extension": ext,
                        "count": count,
                    }
                    for ext, count
                    in file_type_counts.items()
                ],
            }
        )
        return context


class AttachmentAnalyticsCSVView(StaffOnlyMixin, View):
    allowed_chart_types = {
        "all",
        "pdf",
        "txt",
        "images",
        "gif",
        "word",
        "other",
    }
    allowed_date_ranges = {"all", "7", "30", "90"}

    def get(self, request):
        chart_type = request.GET.get("chart_type", "all").strip().lower()
        if chart_type not in self.allowed_chart_types:
            chart_type = "all"

        date_range = request.GET.get("date_range", "all").strip().lower()
        if date_range not in self.allowed_date_ranges:
            date_range = "all"

        attachments = MessageAttachment.objects.all()
        if date_range != "all":
            cutoff_date = timezone.now() - timedelta(days=int(date_range))
            attachments = attachments.filter(uploaded_at__gte=cutoff_date)

        file_type_counts = {
            extension: attachments.filter(file__iendswith=extension).count()
            for extension in AttachmentDashboardView.ALLOWED_EXTENSIONS
        }
        total_attachments = attachments.count()
        known_count = sum(file_type_counts.values())
        image_count = sum(
            file_type_counts[extension]
            for extension in (".jpg", ".jpeg", ".png")
        )
        word_count = file_type_counts[".doc"] + file_type_counts[".docx"]

        categories = [
            ("pdf", "PDF", file_type_counts[".pdf"]),
            ("txt", "TXT", file_type_counts[".txt"]),
            ("images", "Images", image_count),
            ("gif", "GIF", file_type_counts[".gif"]),
            ("word", "Word Documents", word_count),
            ("other", "Other", max(0, total_attachments - known_count)),
        ]
        if chart_type != "all":
            categories = [
                category
                for category in categories
                if category[0] == chart_type
            ]

        generated_at = timezone.localtime()
        date_labels = {
            "all": "All Time",
            "7": "Last 7 Days",
            "30": "Last 30 Days",
            "90": "Last 90 Days",
        }
        selected_type_label = "All" if chart_type == "all" else chart_type.upper()
        date_stamp = generated_at.strftime("%Y-%m-%d")
        filename = (
            f"attachment_analytics_{date_stamp}_"
            f"{chart_type}_{date_range}days.csv"
        )

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow(["Report", "Attachment Analytics"])
        writer.writerow(
            ["Generated", generated_at.strftime("%Y-%m-%d %H:%M:%S")]
        )
        writer.writerow(["Date Range", date_labels[date_range]])
        writer.writerow(["File Type Filter", selected_type_label])
        writer.writerow([])
        writer.writerow(["File Type", "Count"])

        total_count = 0
        for _, label, count in categories:
            writer.writerow([label, count])
            total_count += count

        writer.writerow(["Total", total_count])
        return response


# ==========================================
# DAY 205 - EFFICIENT ATTACHMENT PAGINATION
# ==========================================

class EfficientAttachmentListView(StaffOnlyMixin, ListView):
    model = MessageAttachment

    template_name = "homepage/efficient_attachments.html"
    context_object_name = "attachments"

    paginate_by = 20

    def get_queryset(self):
        return (
            MessageAttachment.objects
            .select_related("contact_message")
            .order_by("-id")
        )
