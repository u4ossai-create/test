

# # # # Register your models here.
# # # from django.contrib import admin
# # # from .models import Staff, Attendance

# # # admin.site.register(Staff)
# # # admin.site.register(Attendance)
# # # #User name admin
# # # #Password – Goodman1
# # from django.contrib import admin
# # from django.utils.html import format_html

# # from .models import Attendance, Device, Person


# # class DeviceInline(admin.TabularInline):
# #     model = Device
# #     extra = 0
# #     readonly_fields = ("device_id", "user_agent", "created_at", "last_seen")


# # @admin.register(Person)
# # class PersonAdmin(admin.ModelAdmin):
# #     list_display = ("employee_id", "full_name", "email", "is_active", "device_count")
# #     list_filter = ("is_active",)
# #     search_fields = ("employee_id", "full_name", "email")
# #     inlines = [DeviceInline]

# #     @admin.display(description="Devices")
# #     def device_count(self, obj):
# #         return obj.devices.filter(is_active=True).count()


# # @admin.register(Device)
# # class DeviceAdmin(admin.ModelAdmin):
# #     list_display = ("person", "label", "device_id", "is_active", "last_seen")
# #     list_filter = ("is_active",)
# #     search_fields = ("person__full_name", "person__employee_id", "label")
# #     readonly_fields = ("device_id", "user_agent", "created_at", "last_seen")


# # @admin.register(Attendance)
# # class AttendanceAdmin(admin.ModelAdmin):
# #     list_display = ("person", "kind", "captured_at", "thumb", "ip_address")
# #     list_filter = ("kind", "captured_at", "person")
# #     search_fields = ("person__full_name", "person__employee_id")
# #     date_hierarchy = "captured_at"
# #     readonly_fields = ("created_at", "thumb")

# #     @admin.display(description="Photo")
# #     def thumb(self, obj):
# #         if not obj.photo:
# #             return "—"
# #         return format_html(
# #             '<img src="{}" style="height:60px;border-radius:6px" />', obj.photo.url
# #         )
# from django.contrib import admin
# from django.utils.html import format_html
# from .models import Attendance, Device, Person


# class DeviceInline(admin.TabularInline):
#     model = Device
#     extra = 0


# @admin.register(Person)
# class PersonAdmin(admin.ModelAdmin):
#     list_display = ("staff_id", "surname", "other_name", "is_active")
#     list_filter = ("is_active",)
#     search_fields = ("staff_id", "surname", "other_name")
#     inlines = [DeviceInline]


# @admin.register(Device)
# class DeviceAdmin(admin.ModelAdmin):
#     list_display = ("person", "label", "device_id", "is_active", "last_seen")
#     list_filter = ("is_active",)


# @admin.register(Attendance)
# class AttendanceAdmin(admin.ModelAdmin):
#     # Updated to match your new table structure
#     list_display = ("person", "date", "time_in", "time_out", "photo_in_thumb", "photo_out_thumb")
#     list_filter = ("date",)
#     search_fields = ("person__surname", "person__staff_id")
#     date_hierarchy = "date"
#     readonly_fields = ("created_at", "photo_in_thumb", "photo_out_thumb")

#     @admin.display(description="In")
#     def photo_in_thumb(self, obj):
#         if not obj.photo_in:
#             return "—"
#         return format_html('<img src="{}" style="height:48px;border-radius:6px" />', obj.photo_in.url)

#     @admin.display(description="Out")
#     def photo_out_thumb(self, obj):
#         if not obj.photo_out:
#             return "—"
#         return format_html('<img src="{}" style="height:48px;border-radius:6px" />', obj.photo_out.url)
from django.contrib import admin
from django.utils.html import format_html
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "surname", "other_name", "date", "time_in", "time_out")
    list_filter = ("date",)
    search_fields = ("staff_id", "surname")
    date_hierarchy = "date"
    ordering = ("-date", "surname")