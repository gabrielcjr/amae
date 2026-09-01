from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic.base import RedirectView

from missions.views import home

urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=staticfiles_storage.url("favicon.ico"), permanent=True
        ),
    ),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", home, name="home"),
    path("", include("accounts.urls")),
    path("", include("missions.urls")),
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
