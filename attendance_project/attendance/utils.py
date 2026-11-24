import re

from django.conf import settings
from django.shortcuts import render


def cfg(key, default=None):
    return getattr(settings, "ATTENDANCE", {}).get(key, default)


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def to_decimal(value):
    from decimal import Decimal, InvalidOperation
    try:
        return Decimal(str(value)).quantize(Decimal("0.000001"))
    except (InvalidOperation, TypeError, ValueError):
        return None


def mobile_only(view):
    """
    Secondary mobile guard for views that must NEVER be reachable from desktop.

    The MobileOnlyMiddleware already rejects desktops globally; this decorator
    exists so the intent is explicit and to survive a config where MOBILE_ONLY
    is temporarily disabled for development.
    """
    from functools import wraps
    from .middleware import is_mobile_request

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if cfg("MOBILE_ONLY", False) and not is_mobile_request(request):
            return render(request, "attendance/desktop_blocked.html", status=403)
        return view(request, *args, **kwargs)

    return wrapper