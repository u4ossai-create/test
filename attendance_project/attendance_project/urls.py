# # # """
# # # URL configuration for attendance_project project.

# # # The `urlpatterns` list routes URLs to views. For more information please see:
# # #     https://docs.djangoproject.com/en/6.1/topics/http/urls/
# # # Examples:
# # # Function views
# # #     1. Add an import:  from my_app import views
# # #     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# # # Class-based views
# # #     1. Add an import:  from other_app.views import Home
# # #     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# # # Including another URLconf
# # #     1. Import the include() function: from django.urls import include, path
# # #     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# # # """
# # # from django.contrib import admin
# # # from django.urls import path, include

# # # urlpatterns = [
# # #     path('admin/', admin.site.urls),
# # #     path('', include('attendance.urls')),
# # # ]
# # from django.conf import settings
# # from django.conf.urls.static import static
# # from django.contrib import admin
# # from django.urls import include, path
# # from django.views.generic import TemplateView

# # urlpatterns = [
# #     path("admin/", admin.site.urls),
# #     path("", include("attendance.urls")),   # include the APP, not the project

# #     path(
# #         "manifest.webmanifest",
# #         TemplateView.as_view(
# #             template_name="attendance/manifest.webmanifest",
# #             content_type="application/manifest+json",
# #         ),
# #         name="manifest",
# #     ),
# #     path(
# #         "sw.js",
# #         TemplateView.as_view(
# #             template_name="attendance/sw.js",
# #             content_type="application/javascript",
# #         ),
# #         name="sw",
# #     ),
# # ]

# # if settings.DEBUG:
# #     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# from django.urls import path

# from . import views

# app_name = "attendance"

# urlpatterns = [
#     path("", views.mark, name="mark"),
#     path("enroll/", views.enroll_device, name="enroll"),
#     path("today/", views.today, name="today"),
#     path("records/", views.attendance_list, name="records"),
#     path("records/export/", views.attendance_export, name="export"),
# ]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("attendance.urls")),

    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="attendance/manifest.webmanifest",
            content_type="application/manifest+json",
        ),
        name="manifest",
    ),
    path(
        "sw.js",
        TemplateView.as_view(
            template_name="attendance/sw.js",
            content_type="application/javascript",
        ),
        name="sw",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)