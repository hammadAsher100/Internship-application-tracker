from django.contrib import admin
from django.urls import include, path

from apps.core.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("apps.accounts.urls")),
]

handler403 = "apps.accounts.views.forbidden"
