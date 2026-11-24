# # from django.urls import path
# # from . import views

# # urlpatterns = [
# #     path('', views.capture_attendance, name='capture_attendance'),
# # ]
# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.urls import include, path
# from django.views.generic import TemplateView

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("", include("attendance.urls")),

#     # PWA files must live at the site root to control the whole scope.
#     path(
#         "manifest.webmanifest",
#         TemplateView.as_view(
#             template_name="attendance/manifest.webmanifest",
#             content_type="application/manifest+json",
#         ),
#         name="manifest",
#     ),
#     path("sw.js", TemplateView.as_view(
#         template_name="attendance/sw.js",
#         content_type="application/javascript",
#     ), name="sw"),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
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
from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.mark, name="mark"),
    path("today/", views.today, name="today"),
    path("records/export/", views.attendance_export, name="export"),
]