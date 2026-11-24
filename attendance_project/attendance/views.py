# # # # # # from datetime import timedelta

# # # # # from django.http import JsonResponse
# # # # # from django.shortcuts import render
# # # # # from django.utils import timezone
# # # # # from django.views.decorators.http import require_http_methods, require_POST

# # # # # from .models import Attendance, Device, Person
# # # # # from .utils import cfg, client_ip, mobile_only, to_decimal

# # # # # ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


# # # # # def _next_kind(person):
# # # # #     today = timezone.localdate()
# # # # #     last = (
# # # # #         person.attendance.filter(captured_at__date=today)
# # # # #         .order_by("-captured_at")
# # # # #         .first()
# # # # #     )
# # # # #     if last is None or last.kind == Attendance.Kind.OUT:
# # # # #         return Attendance.Kind.IN
# # # # #     return Attendance.Kind.OUT


# # # # # def _validate_photo(photo):
# # # # #     if photo is None:
# # # # #         return "No photo was captured."
# # # # #     max_bytes = cfg("MAX_PHOTO_BYTES", 3 * 1024 * 1024)
# # # # #     if photo.size > max_bytes:
# # # # #         return f"Photo is too large (max {max_bytes // 1024 // 1024} MB)."
# # # # #     if photo.content_type not in ALLOWED_IMAGE_TYPES:
# # # # #         return "Unsupported image format. Use JPEG, PNG or WebP."
# # # # #     return None


# # # # # @mobile_only
# # # # # @require_http_methods(["GET", "POST"])
# # # # # def mark(request):
# # # # #     if request.method == "GET":
# # # # #         return render(
# # # # #             request,
# # # # #             "attendance/mark.html",
# # # # #             {
# # # # #                 "require_bound_device": cfg("REQUIRE_BOUND_DEVICE", True),
# # # # #                 "allow_gallery": cfg("ALLOW_GALLERY_UPLOAD", False),
# # # # #             },
# # # # #         )

# # # # #     device_id = (request.POST.get("device_id") or "").strip()
# # # # #     if not device_id:
# # # # #         return JsonResponse({"ok": False, "error": "Missing device id."}, status=400)

# # # # #     device = (
# # # # #         Device.objects.select_related("person")
# # # # #         .filter(device_id=device_id, is_active=True)
# # # # #         .first()
# # # # #     )

# # # # #     if device is None:
# # # # #         if cfg("REQUIRE_BOUND_DEVICE", True):
# # # # #             return JsonResponse(
# # # # #                 {"ok": False, "need_enroll": True,
# # # # #                  "error": "This phone is not registered yet."},
# # # # #                 status=403,
# # # # #             )
# # # # #         person = Person.objects.filter(is_active=True).first()
# # # # #         if person is None:
# # # # #             return JsonResponse({"ok": False, "error": "No active person."}, status=400)
# # # # #         device = Device.objects.create(
# # # # #             person=person, device_id=device_id, label="Unbound device",
# # # # #             user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
# # # # #         )

# # # # #     person = device.person
# # # # #     if not person.is_active:
# # # # #         return JsonResponse({"ok": False, "error": "Account is inactive."}, status=403)

# # # # #     photo = request.FILES.get("photo")
# # # # #     error = _validate_photo(photo)
# # # # #     if error:
# # # # #         return JsonResponse({"ok": False, "error": error}, status=400)

# # # # #     cooldown = cfg("DUPLICATE_COOLDOWN_SECONDS", 60)
# # # # #     if cooldown:
# # # # #         cutoff = timezone.now() - timedelta(seconds=cooldown)
# # # # #         if person.attendance.filter(created_at__gte=cutoff).exists():
# # # # #             return JsonResponse(
# # # # #                 {"ok": False, "error": "Already recorded a moment ago."}, status=429
# # # # #             )

# # # # #     kind = request.POST.get("kind", "")
# # # # #     if kind not in Attendance.Kind.values:
# # # # #         kind = _next_kind(person)

# # # # #     record = Attendance(
# # # # #         person=person, device=device, kind=kind,
# # # # #         latitude=to_decimal(request.POST.get("latitude")),
# # # # #         longitude=to_decimal(request.POST.get("longitude")),
# # # # #         ip_address=client_ip(request),
# # # # #         note=(request.POST.get("note") or "")[:200],
# # # # #     )
# # # # #     stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
# # # # #     record.photo.save(f"{person.employee_id}-{stamp}.jpg", photo, save=False)
# # # # #     record.save()
# # # # #     Device.objects.filter(pk=device.pk).update(last_seen=timezone.now())

# # # # #     label = "Checked in" if kind == Attendance.Kind.IN else "Checked out"
# # # # #     return JsonResponse({
# # # # #         "ok": True, "kind": kind,
# # # # #         "message": f"{label} at {timezone.localtime(record.captured_at):%H:%M}",
# # # # #         "record_id": record.pk,
# # # # #         "redirect": request.build_absolute_uri("/today/"),
# # # # #     })


# # # # # @mobile_only
# # # # # @require_POST
# # # # # def enroll_device(request):
# # # # #     employee_id = (request.POST.get("employee_id") or "").strip()
# # # # #     pin = (request.POST.get("pin") or "").strip()
# # # # #     device_id = (request.POST.get("device_id") or "").strip()
# # # # #     label = (request.POST.get("label") or "").strip()[:100]

# # # # #     if not (employee_id and pin and device_id):
# # # # #         return JsonResponse(
# # # # #             {"ok": False, "error": "Employee ID, PIN and device are required."},
# # # # #             status=400,
# # # # #         )

# # # # #     person = Person.objects.filter(
# # # # #         employee_id__iexact=employee_id, is_active=True
# # # # #     ).first()
# # # # #     if person is None or not person.check_pin(pin):
# # # # #         return JsonResponse({"ok": False, "error": "Invalid ID or PIN."}, status=403)

# # # # #     if Device.objects.filter(device_id=device_id).exists():
# # # # #         return JsonResponse(
# # # # #             {"ok": False, "error": "This phone is already registered."}, status=409
# # # # #         )

# # # # #     limit = cfg("MAX_DEVICES_PER_PERSON", 2)
# # # # #     if person.devices.filter(is_active=True).count() >= limit:
# # # # #         return JsonResponse(
# # # # #             {"ok": False,
# # # # #              "error": f"Device limit reached ({limit}). Ask an admin to reset."},
# # # # #             status=403,
# # # # #         )

# # # # #     Device.objects.create(
# # # # #         person=person, device_id=device_id, label=label or "Phone",
# # # # #         user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
# # # # #     )
# # # # #     return JsonResponse({"ok": True, "message": "Phone registered."})


# # # # # def today(request):
# # # # #     day = timezone.localdate()
# # # # #     records = (
# # # # #         Attendance.objects.select_related("person", "device")
# # # # #         .filter(captured_at__date=day)
# # # # #         .order_by("-captured_at")
# # # # #     )
# # # # #     return render(request, "attendance/today.html", {"records": records, "day": day})


# # # # # def attendance_list(request):
# # # # #     """Read-only records viewer — enforced phone-only by the middleware."""
# # # # #     from django.core.paginator import Paginator
# # # # #     from django.db.models import Q

# # # # #     qs = Attendance.objects.select_related("person", "device").order_by("-captured_at")

# # # # #     person_q = (request.GET.get("person") or "").strip()
# # # # #     if person_q:
# # # # #         qs = qs.filter(
# # # # #             Q(person__full_name__icontains=person_q)
# # # # #             | Q(person__employee_id__icontains=person_q)
# # # # #         )

# # # # #     kind = (request.GET.get("kind") or "").strip()
# # # # #     if kind in Attendance.Kind.values:
# # # # #         qs = qs.filter(kind=kind)

# # # # #     date_from = (request.GET.get("from") or "").strip()
# # # # #     if date_from:
# # # # #         qs = qs.filter(captured_at__date__gte=date_from)

# # # # #     date_to = (request.GET.get("to") or "").strip()
# # # # #     if date_to:
# # # # #         qs = qs.filter(captured_at__date__lte=date_to)

# # # # #     paginator = Paginator(qs, 50)
# # # # #     page = paginator.get_page(request.GET.get("page"))

# # # # #     params = request.GET.copy()
# # # # #     params.pop("page", None)

# # # # #     return render(request, "attendance/attendance_list.html", {
# # # # #         "page": page, "total": qs.count(),
# # # # #         "person_q": person_q, "kind": kind,
# # # # #         "date_from": date_from, "date_to": date_to,
# # # # #         "querystring": params.urlencode(),
# # # # #         "kinds": Attendance.Kind.choices,
# # # # #     })


# # # # # def attendance_export(request):
# # # # #     """CSV export — only reachable from a phone (middleware enforces)."""
# # # # #     import csv
# # # # #     from django.http import HttpResponse

# # # # #     response = HttpResponse(content_type="text/csv")
# # # # #     stamp = timezone.localtime().strftime("%Y%m%d-%H%M")
# # # # #     response["Content-Disposition"] = f'attachment; filename="attendance-{stamp}.csv"'

# # # # #     writer = csv.writer(response)
# # # # #     writer.writerow(["Date", "Time", "Employee ID", "Name", "Kind",
# # # # #                      "Device", "IP", "Latitude", "Longitude", "Photo URL"])

# # # # #     qs = Attendance.objects.select_related("person", "device").order_by("-captured_at")
# # # # #     for r in qs.iterator():
# # # # #         local = timezone.localtime(r.captured_at)
# # # # #         writer.writerow([
# # # # #             local.strftime("%Y-%m-%d"), local.strftime("%H:%M:%S"),
# # # # #             r.person.employee_id, r.person.full_name, r.get_kind_display(),
# # # # #             r.device.label if r.device else "", r.ip_address or "",
# # # # #             r.latitude or "", r.longitude or "",
# # # # #             request.build_absolute_uri(r.photo.url) if r.photo else "",
# # # # #         ])
# # # # #     return response
# # # # from django.http import JsonResponse, HttpResponse
# # # # from django.shortcuts import render
# # # # from django.utils import timezone
# # # # from django.views.decorators.http import require_http_methods
# # # # from .models import Attendance, Person
# # # # from .utils import mobile_only, client_ip
# # # # import csv

# # # # def _find_person(query):
# # # #     q = (query or "").strip()
# # # #     if not q:
# # # #         return None
# # # #     return Person.objects.filter(is_active=True).filter(
# # # #         models.Q(staff_id__iexact=q) | models.Q(surname__icontains=q)
# # # #     ).first()

# # # # @mobile_only
# # # # @require_http_methods(["GET", "POST"])
# # # # def mark(request):
# # # #     if request.method == "GET":
# # # #         return render(request, "attendance/mark.html", {})

# # # #     action = (request.POST.get("action") or "").strip()  # "in" or "out"
# # # #     query = (request.POST.get("query") or "").strip()
    
# # # #     from django.db.models import Q
# # # #     person = Person.objects.filter(is_active=True).filter(
# # # #         Q(staff_id__iexact=query) | Q(surname__icontains=query)
# # # #     ).first()

# # # #     if not person:
# # # #         return JsonResponse({"ok": False, "error": "No staff found for that surname or ID."}, status=404)

# # # #     photo = request.FILES.get("photo")
# # # #     if not photo:
# # # #         return JsonResponse({"ok": False, "error": "No photo captured."}, status=400)

# # # #     today = timezone.localdate()
# # # #     now = timezone.now()
    
# # # #     # Check if there is an open shift (clocked in but not clocked out)
# # # #     open_shift = Attendance.objects.filter(person=person, date=today, time_out__isnull=True).first()

# # # #     if action == "in":
# # # #         if open_shift:
# # # #             return JsonResponse({"ok": False, "error": "Already clocked in. Clock out first."}, status=409)
        
# # # #         log = Attendance(person=person, date=today, time_in=now, ip_address=client_ip(request))
# # # #         log.photo_in.save(f"{person.staff_id}-in.jpg", photo, save=False)
# # # #         log.save()
# # # #         return JsonResponse({"ok": True, "message": f"{person.surname} clocked in at {timezone.localtime(now):%H:%M}"})

# # # #     elif action == "out":
# # # #         if not open_shift:
# # # #             return JsonResponse({"ok": False, "error": "You have not clocked in yet today."}, status=409)
        
# # # #         open_shift.time_out = now
# # # #         open_shift.photo_out.save(f"{person.staff_id}-out.jpg", photo, save=False)
# # # #         open_shift.save()
# # # #         return JsonResponse({"ok": True, "message": f"{person.surname} clocked out at {timezone.localtime(now):%H:%M}"})

# # # #     return JsonResponse({"ok": False, "error": "Invalid action."}, status=400)


# # # # @mobile_only
# # # # def today(request):
# # # #     day = timezone.localdate()
# # # #     logs = Attendance.objects.select_related("person").filter(date=day).order_by("-time_in")
# # # #     return render(request, "attendance/today.html", {"logs": logs, "day": day})


# # # # def attendance_export(request):
# # # #     response = HttpResponse(content_type="text/csv")
# # # #     response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
    
# # # #     writer = csv.writer(response)
# # # #     writer.writerow(["Surname", "Other_Name", "Staff_Id", "Date", "Time_In", "Time_Out"])
    
# # # #     qs = Attendance.objects.select_related("person").order_by("-date", "person__surname")
# # # #     for log in qs:
# # # #         tin = timezone.localtime(log.time_in).strftime("%H:%M") if log.time_in else ""
# # # #         tout = timezone.localtime(log.time_out).strftime("%H:%M") if log.time_out else ""
# # # #         writer.writerow([
# # # #             log.person.surname, 
# # # #             log.person.other_name, 
# # # #             log.person.staff_id, 
# # # #             log.date.strftime("%a %d %B, %Y"), 
# # # #             tin, 
# # # #             tout
# # # #         ])
# # # #     return response
# # # from django.http import JsonResponse
# # # from django.shortcuts import render
# # # from django.utils import timezone
# # # from django.db.models import Q
# # # from .models import Attendance
# # # from .utils import mobile_only

# # # @mobile_only
# # # def mark(request):
# # #     if request.method == "GET":
# # #         return render(request, "attendance/mark.html")

# # #     action = (request.POST.get("action") or "").strip()
# # #     query = (request.POST.get("query") or "").strip()
# # #     photo = request.FILES.get("photo")

# # #     if not query:
# # #         return JsonResponse({"ok": False, "error": "Enter your surname or staff ID."}, status=400)
    
# # #     if not photo:
# # #         return JsonResponse({"ok": False, "error": "No photo captured."}, status=400)

# # #     # Look up the staff member in your existing table
# # #     last_record = Attendance.objects.filter(
# # #         Q(staff_id__iexact=query) | Q(surname__icontains=query)
# # #     ).order_by('-attendance_id').first()

# # #     if last_record:
# # #         staff_id = last_record.staff_id
# # #         surname = last_record.surname
# # #         other_name = last_record.other_name
# # #     else:
# # #         # If they don't exist at all, we just use what they typed as the surname
# # #         staff_id = query
# # #         surname = query
# # #         other_name = ""

# # #     today = timezone.localdate()
# # #     now_time = timezone.localtime(timezone.now()).time()

# # #     if action == "in":
# # #         # Create a new row for the clock-in
# # #         log = Attendance(
# # #             staff_id=staff_id,
# # #             surname=surname,
# # #             other_name=other_name,
# # #             date=today,
# # #             time_in=now_time
# # #         )
# # #         log.photo_in.save(f"{staff_id}-in-{today}.jpg", photo, save=False)
# # #         log.save()
# # #         return JsonResponse({"ok": True, "message": f"{surname} clocked in at {now_time.strftime('%H:%M')}"})

# # #     elif action == "out":
# # #         # Find today's open shift
# # #         open_shift = Attendance.objects.filter(
# # #             staff_id=staff_id, 
# # #             date=today, 
# # #             time_out__isnull=True
# # #         ).order_by('-attendance_id').first()

# # #         if not open_shift:
# # #             return JsonResponse({"ok": False, "error": "You have not clocked in yet today."}, status=409)
        
# # #         open_shift.time_out = now_time
# # #         open_shift.photo_out.save(f"{staff_id}-out-{today}.jpg", photo, save=False)
# # #         open_shift.save()
# # #         return JsonResponse({"ok": True, "message": f"{surname} clocked out at {now_time.strftime('%H:%M')}"})

# # #     return JsonResponse({"ok": False, "error": "Invalid action."}, status=400)


# # # @mobile_only
# # # def today(request):
# # #     day = timezone.localdate()
# # #     logs = Attendance.objects.filter(date=day).order_by("-time_in")
# # #     return render(request, "attendance/today.html", {"logs": logs, "day": day})


# # # def attendance_export(request):
# # #     import csv
# # #     from django.http import HttpResponse

# # #     response = HttpResponse(content_type="text/csv")
# # #     response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
    
# # #     writer = csv.writer(response)
# # #     writer.writerow(["Surname", "Other_Name", "Staff_Id", "Date", "Time_In", "Time_Out"])
    
# # #     qs = Attendance.objects.all().order_by("-date", "surname")
# # #     for log in qs:
# # #         tin = log.time_in.strftime("%H:%M") if log.time_in else ""
# # #         tout = log.time_out.strftime("%H:%M") if log.time_out else ""
# # #         writer.writerow([
# # #             log.surname, 
# # #             log.other_name, 
# # #             log.staff_id, 
# # #             log.date.strftime("%a %d %B, %Y"), 
# # #             tin, 
# # #             tout
# # #         ])
# # #     return response
# # from django.http import JsonResponse, HttpResponse
# # from django.shortcuts import render
# # from django.utils import timezone
# # from django.db.models import Q
# # from .models import Attendance
# # from .utils import mobile_only
# # import csv

# # @mobile_only
# # def mark(request):
# #     if request.method == "GET":
# #         return render(request, "attendance/mark.html")

# #     action = (request.POST.get("action") or "").strip()
# #     query = (request.POST.get("query") or "").strip()
# #     photo = request.FILES.get("photo")

# #     if not query:
# #         return JsonResponse({"ok": False, "error": "Enter your surname or staff ID."}, status=400)
    
# #     if not photo:
# #         return JsonResponse({"ok": False, "error": "No photo captured."}, status=400)

# #     # Look up the staff member in your existing table
# #     last_record = Attendance.objects.filter(
# #         Q(staff_id__iexact=query) | Q(surname__icontains=query)
# #     ).order_by('-attendance_id').first()

# #     if last_record:
# #         staff_id = last_record.staff_id
# #         surname = last_record.surname
# #         other_name = last_record.other_name
# #     else:
# #         # If they don't exist at all, we just use what they typed as the surname
# #         staff_id = query
# #         surname = query
# #         other_name = ""

# #     today = timezone.localdate()
# #     now_time = timezone.localtime(timezone.now()).time()

# #     if action == "in":
# #         # Create a new row for the clock-in
# #         log = Attendance(
# #             staff_id=staff_id,
# #             surname=surname,
# #             other_name=other_name,
# #             date=today,
# #             time_in=now_time
# #         )
# #         log.photo_in.save(f"{staff_id}-in-{today}.jpg", photo, save=False)
# #         log.save()
# #         return JsonResponse({"ok": True, "message": f"{surname} clocked in at {now_time.strftime('%H:%M')}"})

# #     elif action == "out":
# #         # Find today's open shift
# #         open_shift = Attendance.objects.filter(
# #             staff_id=staff_id, 
# #             date=today, 
# #             time_out__isnull=True
# #         ).order_by('-attendance_id').first()

# #         if not open_shift:
# #             return JsonResponse({"ok": False, "error": "You have not clocked in yet today."}, status=409)
        
# #         open_shift.time_out = now_time
# #         open_shift.photo_out.save(f"{staff_id}-out-{today}.jpg", photo, save=False)
# #         open_shift.save()
# #         return JsonResponse({"ok": True, "message": f"{surname} clocked out at {now_time.strftime('%H:%M')}"})

# #     return JsonResponse({"ok": False, "error": "Invalid action."}, status=400)


# # @mobile_only
# # def today(request):
# #     day = timezone.localdate()
# #     logs = Attendance.objects.filter(date=day).order_by("-time_in")
# #     return render(request, "attendance/today.html", {"logs": logs, "day": day})


# # def attendance_export(request):
# #     response = HttpResponse(content_type="text/csv")
# #     response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
    
# #     writer = csv.writer(response)
# #     writer.writerow(["Surname", "Other_Name", "Staff_Id", "Date", "Time_In", "Time_Out"])
    
# #     qs = Attendance.objects.all().order_by("-date", "surname")
# #     for log in qs:
# #         tin = log.time_in.strftime("%H:%M") if log.time_in else ""
# #         tout = log.time_out.strftime("%H:%M") if log.time_out else ""
# #         writer.writerow([
# #             log.surname, 
# #             log.other_name, 
# #             log.staff_id, 
# #             log.date.strftime("%a %d %B, %Y"), 
# #             tin, 
# #             tout
# #         ])
# #     return response
# from django.http import JsonResponse, HttpResponse
# from django.shortcuts import render
# from django.utils import timezone
# from django.db.models import Q
# from .models import Attendance
# from .utils import mobile_only
# import csv
# @mobile_only
# def mark(request):
#     if request.method == "GET":
#         return render(request, "attendance/mark.html")

#     try:
#         action = (request.POST.get("action") or "").strip()
#         query = (request.POST.get("query") or "").strip()
#         photo = request.FILES.get("photo")

#         if not query:
#             return JsonResponse({"ok": False, "error": "Enter your surname or staff ID."}, status=400)
        
#         if not photo:
#             return JsonResponse({"ok": False, "error": "No photo captured."}, status=400)

#         last_record = Attendance.objects.filter(
#             Q(staff_id__iexact=query) | Q(surname__icontains=query)
#         ).order_by('-attendance_id').first()

#         if last_record:
#             staff_id = last_record.staff_id
#             surname = last_record.surname
#             other_name = last_record.other_name
#         else:
#             staff_id = query
#             surname = query
#             other_name = ""

#         today = timezone.localdate()
#         now_time = timezone.localtime(timezone.now()).time()

#         if action == "in":
#             log = Attendance(
#                 staff_id=staff_id,
#                 surname=surname,
#                 other_name=other_name,
#                 date=today,
#                 time_in=now_time
#             )
#             log.photo_in.save(f"{staff_id}-in-{today}.jpg", photo, save=False)
#             log.save()
#             return JsonResponse({"ok": True, "message": f"{surname} clocked in at {now_time.strftime('%H:%M')}"})

#         elif action == "out":
#             open_shift = Attendance.objects.filter(
#                 staff_id=staff_id, 
#                 date=today, 
#                 time_out__isnull=True
#             ).order_by('-attendance_id').first()

#             if not open_shift:
#                 return JsonResponse({"ok": False, "error": "You have not clocked in yet today."}, status=409)
            
#             open_shift.time_out = now_time
#             open_shift.photo_out.save(f"{staff_id}-out-{today}.jpg", photo, save=False)
#             open_shift.save()
#             return JsonResponse({"ok": True, "message": f"{surname} clocked out at {now_time.strftime('%H:%M')}"})

#         return JsonResponse({"ok": False, "error": "Invalid action."}, status=400)
        
#     except Exception as e:
#         # THIS WILL SEND THE EXACT POSTGRESQL ERROR TO YOUR PHONE
#         return JsonResponse({"ok": False, "error": f"DATABASE ERROR: {str(e)}"}, status=500)

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from .models import Attendance
from .utils import mobile_only
import csv

@mobile_only
def mark(request):
    if request.method == "GET":
        return render(request, "attendance/mark.html")

    try:
        action = (request.POST.get("action") or "").strip()
        query = (request.POST.get("query") or "").strip()
        photo = request.FILES.get("photo")

        if not query:
            return JsonResponse({"ok": False, "error": "Enter your surname or staff ID."}, status=400)
        
        if not photo:
            return JsonResponse({"ok": False, "error": "No photo captured."}, status=400)

        # Look up the staff member in your existing table
        last_record = Attendance.objects.filter(
            Q(staff_id__iexact=query) | Q(surname__icontains=query)
        ).order_by('-attendance_id').first()

        if last_record:
            staff_id = last_record.staff_id
            surname = last_record.surname
            other_name = last_record.other_name
        else:
            # If they don't exist at all, we just use what they typed as the surname
            staff_id = query
            surname = query
            other_name = ""

        today = timezone.localdate()
        now_time = timezone.localtime(timezone.now()).time()

        if action == "in":
            # Create a new row for the clock-in
            log = Attendance(
                staff_id=staff_id,
                surname=surname,
                other_name=other_name,
                date=today,
                time_in=now_time
            )
            log.photo_in.save(f"{staff_id}-in-{today}.jpg", photo, save=False)
            log.save()
            return JsonResponse({"ok": True, "message": f"{surname} clocked in at {now_time.strftime('%H:%M')}"})

        elif action == "out":
            # Find today's open shift
            open_shift = Attendance.objects.filter(
                staff_id=staff_id, 
                date=today, 
                time_out__isnull=True
            ).order_by('-attendance_id').first()

            if not open_shift:
                return JsonResponse({"ok": False, "error": "You have not clocked in yet today."}, status=409)
            
            open_shift.time_out = now_time
            open_shift.photo_out.save(f"{staff_id}-out-{today}.jpg", photo, save=False)
            open_shift.save()
            return JsonResponse({"ok": True, "message": f"{surname} clocked out at {now_time.strftime('%H:%M')}"})

        return JsonResponse({"ok": False, "error": "Invalid action."}, status=400)
        
    except Exception as e:
        # This will send the exact PostgreSQL error to your phone
        return JsonResponse({"ok": False, "error": f"DATABASE ERROR: {str(e)}"}, status=500)


@mobile_only
def today(request):
    day = timezone.localdate()
    logs = Attendance.objects.filter(date=day).order_by("-time_in")
    return render(request, "attendance/today.html", {"logs": logs, "day": day})


def attendance_export(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
    
    writer = csv.writer(response)
    writer.writerow(["Surname", "Other_Name", "Staff_Id", "Date", "Time_In", "Time_Out"])
    
    qs = Attendance.objects.all().order_by("-date", "surname")
    for log in qs:
        tin = log.time_in.strftime("%H:%M") if log.time_in else ""
        tout = log.time_out.strftime("%H:%M") if log.time_out else ""
        writer.writerow([
            log.surname, 
            log.other_name, 
            log.staff_id, 
            log.date.strftime("%a %d %B, %Y"), 
            tin, 
            tout
        ])
    return response