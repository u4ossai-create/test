import logging
import re

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)

# Paths that never require a phone.
EXEMPT_PREFIXES = (
    "/admin/",
    "/static/",
    "/media/",
    "/favicon.ico",
    "/manifest.webmanifest",
    "/sw.js",
    "/robots.txt",
)

# Any of these tokens → treat as a mobile device.
MOBILE_UA_RE = re.compile(
    r"Android|iPhone|iPod|iPad|Mobile|Windows Phone|webOS|"
    r"BlackBerry|Opera Mini|IEMobile|Mobile Safari|CriOS|FxiOS|"
    r"SamsungBrowser|MiuiBrowser|HeyTapBrowser|OppoBrowser|"
    r"VivoBrowser|HuaweiBrowser|UCBrowser|DuckDuckGo|FBAN|FBAV|"
    r"Instagram|WhatsApp|EdgA|EdgiOS|Tablet|Kindle|Silk",
    re.IGNORECASE,
)

# Strong desktop signals. Only reject when one is present AND no mobile token
# matched. Note: Android UAs contain "Linux; Android ..." and iPhone UAs
# contain "like Mac OS X" — neither of those is listed here on purpose.
DESKTOP_UA_RE = re.compile(
    r"Windows NT|Macintosh; Intel|Macintosh; PPC|"
    r"X11; Linux x86_64|X11; Linux i686|X11; Ubuntu|X11; Fedora|CrOS",
    re.IGNORECASE,
)


def _is_exempt(path: str) -> bool:
    return any(path.startswith(p) for p in EXEMPT_PREFIXES)


def _ua_says_mobile(ua: str) -> bool:
    if not ua:
        return False
    # Positive mobile signal wins immediately, even if a desktop-ish word
    # also appears. Android UAs contain "Linux", iPhone UAs contain
    # "like Mac OS X" — both are phones despite the desktop-looking tokens.
    return bool(MOBILE_UA_RE.search(ua))


def _ua_says_desktop(ua: str) -> bool:
    if not ua:
        return False
    return bool(DESKTOP_UA_RE.search(ua))


def _client_hints_say_mobile(request):
    """Chromium sends Sec-CH-UA-Mobile: ?1 on phones. None if absent."""
    hint = request.META.get("HTTP_SEC_CH_UA_MOBILE")
    if hint is None:
        return None
    return hint.strip() == "?1"


def is_mobile_request(request) -> bool:
    ua = request.META.get("HTTP_USER_AGENT", "")

    # 1) Positive mobile UA → allow.
    if _ua_says_mobile(ua):
        return True

    # 2) Client Hint explicitly says mobile → allow.
    if _client_hints_say_mobile(request) is True:
        return True

    # 3) Strong desktop UA → reject.
    if _ua_says_desktop(ua):
        return False

    # 4) Unknown UA → default to allow so real phones are never locked out.
    #    Set ATTENDANCE['STRICT_UA'] = True in settings to flip this to reject.
    return not getattr(settings, "ATTENDANCE", {}).get("STRICT_UA", False)


class MobileOnlyMiddleware:
    """
    Reject non-exempt requests from anything that isn't a phone.

    Disable globally with ATTENDANCE['MOBILE_ONLY'] = False in settings.py.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "ATTENDANCE", {}).get("MOBILE_ONLY", False):
            return self.get_response(request)

        # Debug helper — open /?ua_debug=1 on the phone to see what the
        # server actually receives.
        if request.GET.get("ua_debug") == "1":
            ua = request.META.get("HTTP_USER_AGENT", "(none)")
            hint = request.META.get("HTTP_SEC_CH_UA_MOBILE", "(none)")
            return HttpResponse(
                "<pre>"
                f"UA: {ua}\n\n"
                f"Sec-CH-UA-Mobile: {hint}\n\n"
                f"is_mobile_request: {is_mobile_request(request)}\n"
                f"path: {request.path}\n"
                f"host: {request.get_host()}\n"
                "</pre>",
                content_type="text/html",
            )

        if _is_exempt(request.path):
            return self.get_response(request)

        if not is_mobile_request(request):
            logger.info(
                "MobileOnly blocked: UA=%r path=%r",
                request.META.get("HTTP_USER_AGENT", ""),
                request.path,
            )
            return render(
                request,
                "attendance/desktop_blocked.html",
                {"requested_path": request.path},
                status=403,
            )

        return self.get_response(request)