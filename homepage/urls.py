from .report_category_list_views import ReportCategoryListView
from .report_category_manage_views import (
    ReportCategoryUpdateView,
    ReportCategoryDeleteView,
)
from .report_category_views import ReportCategoryCreateView
from .aggregation_reports import AttachmentSummaryReportView
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views


# =====================================
# HOMEPAGE APPLICATION URLS
# =====================================

urlpatterns = [

path(
    "reports/categories/",
    ReportCategoryListView.as_view(),
    name="report_category_list",
),

path(
    "reports/categories/<int:pk>/edit/",
    ReportCategoryUpdateView.as_view(),
    name="report_category_update",
),
path(
    "reports/categories/<int:pk>/delete/",
    ReportCategoryDeleteView.as_view(),
    name="report_category_delete",
),
path(
    "reports/categories/create/",
    ReportCategoryCreateView.as_view(),
    name="report_category_create",
),

path(
    "reports/attachment-summary/",
    AttachmentSummaryReportView.as_view(),
    name="attachment_summary_report",
),

    # =====================================
    # DAY 182 - MESSAGE BROWSER
    # =====================================

    path(
        "messages/browse/",
        views.ContactMessageListView.as_view(),
        name="message_browse"
    ),

    path(
        "messages/view/<int:pk>/",
        views.ContactMessageDetailView.as_view(),
        name="message_detail"
    ),

    # =====================================
    # DAY 184 - DELETE URL
    # =====================================

    path(
        "messages/delete/<int:pk>/",
        views.ContactMessageDeleteView.as_view(),
        name="message_delete"
    ),

    # =====================================
    # DAY 183 - CREATE AND UPDATE URLS
    # =====================================

    path(
        "messages/create/",
        views.ContactMessageCreateView.as_view(),
        name="message_create"
    ),

    path(
        "messages/edit/<int:pk>/",
        views.ContactMessageUpdateView.as_view(),
        name="message_edit"
    ),

    # =====================================
    # DAY 191 - REPLACE ATTACHMENT
    # =====================================

    path(
        "attachments/<int:pk>/replace/",
        views.MessageAttachmentReplaceView.as_view(),
        name="message_attachment_replace"
    ),

    # =====================================
    # DAY 192 - ATTACHMENT DASHBOARD
    # =====================================

    path(
        "attachments/dashboard/",
        views.AttachmentDashboardView.as_view(),
        name="attachment_dashboard"
    ),

path(
    "attachments/efficient/",
    views.EfficientAttachmentListView.as_view(),
    name="efficient_attachment_list"
),

    # =====================================
    # DAY 198 - CSV ANALYTICS EXPORT
    # =====================================

    path(
        "attachments/analytics/export/",
        views.AttachmentAnalyticsCSVView.as_view(),
        name="attachment_analytics_csv"
    ),

    # =====================================
    # DAY 186 - ADD NOTE
    # =====================================

    path(
        "messages/view/<int:pk>/add-note/",
        views.MessageNoteFormView.as_view(),
        name="message_add_note"
    ),

    # =====================================
    # DAY 188 - FILE UPLOAD / DOWNLOAD
    # =====================================

    path(
        "messages/view/<int:pk>/upload/",
        views.MessageAttachmentCreateView.as_view(),
        name="message_attachment_upload"
    ),

    path(
        "messages/attachments/<int:attachment_id>/download/",
        views.download_message_attachment,
        name="message_attachment_download"
    ),

    # =====================================
    # DAY 189 - DELETE ATTACHMENT
    # =====================================

    path(
        "messages/attachments/<int:pk>/delete/",
        views.MessageAttachmentDeleteView.as_view(),
        name="message_attachment_delete"
    ),

    # =====================================
    # MAIN WEBSITE PAGES
    # =====================================

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "about/",
        views.about,
        name="about"
    ),

    path(
        "contact/",
        views.contact,
        name="contact"
    ),

    # =====================================
    # STAFF CONTACT MESSAGES
    # =====================================

    path(
        "messages/",
        views.message_list,
        name="message_list"
    ),

    # =====================================
    # LOGIN
    # =====================================

    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="homepage/login.html"
        ),
        name="login"
    ),

    # =====================================
    # LOGOUT - POST REQUEST
    # =====================================

    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(
            next_page="home"
        ),
        name="logout"
    ),

    # =====================================
    # SIGNUP
    # =====================================

    path(
        "accounts/signup/",
        views.signup,
        name="signup"
    ),

    # =====================================
    # USER PROFILE
    # =====================================

    path(
        "accounts/profile/",
        views.profile,
        name="profile"
    ),

    # =====================================
    # PASSWORD CHANGE
    # =====================================

    path(
        "accounts/password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="homepage/password_change.html",
            success_url=reverse_lazy(
                "password_change_done"
            )
        ),
        name="password_change"
    ),

    path(
        "accounts/password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="homepage/password_change_done.html"
        ),
        name="password_change_done"
    ),

    # =====================================
    # PASSWORD RESET
    # =====================================

    path(
        "accounts/password/reset/",
        auth_views.PasswordResetView.as_view(
            template_name="homepage/password_reset_form.html",
            email_template_name="homepage/password_reset_email.txt",
            subject_template_name="homepage/password_reset_subject.txt",
            success_url=reverse_lazy(
                "password_reset_done"
            )
        ),
        name="password_reset"
    ),

    path(
        "accounts/password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="homepage/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "accounts/password/reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="homepage/password_reset_confirm.html",
            success_url=reverse_lazy(
                "password_reset_complete"
            )
        ),
        name="password_reset_confirm"
    ),

    path(
        "accounts/password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="homepage/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),

    # =====================================
    # DAY 181 - CLASS-BASED VIEW
    # =====================================

    path(
        "learning/",
        views.LearningHubView.as_view(),
        name="learning_hub"
    ),

]
