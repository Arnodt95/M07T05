"""
Project URL configuration for news_app_project.

Routes:
- Admin
- Web routes (news_app.urls)
- API routes (news_app.urls_api)
"""
from django.contrib import admin
from django.urls import path, include
from news_app.views import home

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("news_app.urls")),
    path("api/", include("news_app.urls_api")),
]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
