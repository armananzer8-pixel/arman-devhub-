from django.contrib import admin
from django.urls import path, include


# =====================================
# MAIN PROJECT URL CONFIGURATION
# =====================================

urlpatterns = [

    # Django Admin
    path("admin/", admin.site.urls),

    # Homepage App URLs
    path("", include("homepage.urls")),

]