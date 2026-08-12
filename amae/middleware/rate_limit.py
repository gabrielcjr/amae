import functools
import re
import time
from typing import Callable, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, HttpResponseBase


def parse_rate(rate_str: str) -> Tuple[int, int]:
    """
    Parses a rate string like '100/m', '10/s', '1000/h', '50/d' into (count, period_in_seconds).
    Defaults to (100, 60) if parsing fails.
    """
    if not rate_str:
        return 100, 60

    match = re.match(r"^(\d+)/([smhd])$", rate_str.strip().lower())
    if not match:
        return 100, 60

    count = int(match.group(1))
    unit = match.group(2)

    periods = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }
    return count, periods.get(unit, 60)


def get_client_ip(request: HttpRequest) -> str:
    """
    Extracts the client's IP address from HTTP headers or REMOTE_ADDR.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def get_client_identifier(request: HttpRequest) -> str:
    """
    Returns a unique identifier for the request client (authenticated User ID or IP).
    """
    if hasattr(request, "user") and request.user and request.user.is_authenticated:
        return f"user_{request.user.pk}"
    return f"ip_{get_client_ip(request)}"


def is_rate_limited(
    key_prefix: str, identifier: str, limit: int, period: int
) -> Tuple[bool, int]:
    """
    Checks if a given key has exceeded the limit in the current time window.
    Returns (is_limited, retry_after_seconds).
    """
    now = int(time.time())
    window = now // period
    cache_key = f"ratelimit:{key_prefix}:{identifier}:{window}"

    added = cache.add(cache_key, 1, timeout=period + 1)
    if not added:
        try:
            count = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=period + 1)
            count = 1
    else:
        count = 1

    retry_after = max(1, (window + 1) * period - now)
    if count > limit:
        return True, retry_after
    return False, 0


def build_rate_limit_response(retry_after: int, is_htmx: bool = False) -> HttpResponse:
    """
    Builds a 429 Too Many Requests response with Retry-After header.
    """
    msg = f"Muitas requisições. Por favor, aguarde {retry_after} segundos antes de tentar novamente."
    if is_htmx:
        response = HttpResponse(
            f"<div class='p-4 bg-red-100 text-red-700 rounded-md'>{msg}</div>",
            status=429,
            content_type="text/html; charset=utf-8",
        )
    else:
        response = HttpResponse(
            msg,
            status=429,
            content_type="text/plain; charset=utf-8",
        )
    response["Retry-After"] = str(retry_after)
    return response


def is_htmx_request(request: HttpRequest) -> bool:
    """
    Checks if request is an HTMX request.
    """
    return bool(
        (hasattr(request, "htmx") and request.htmx)
        or request.headers.get("HX-Request") == "true"
        or request.META.get("HTTP_HX_REQUEST") == "true"
    )


class RateLimitMiddleware:
    """
    Django middleware to rate limit incoming requests globally and per endpoint category.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        # Check if rate limiting is enabled
        enabled = getattr(settings, "RATELIMIT_ENABLE", True)
        if not enabled:
            return self.get_response(request)

        # Exempt static assets and media files
        path = request.path
        if path.startswith("/static/") or path.startswith("/media/"):
            return self.get_response(request)

        identifier = get_client_identifier(request)
        is_htmx = is_htmx_request(request)

        # Determine rate limit configuration
        auth_paths = (
            "/login/",
            "/logout/",
            "/register/",
            "/contas/",
        )
        is_auth_route = any(path.startswith(auth_p) for auth_p in auth_paths)

        if is_auth_route:
            rate_setting = getattr(settings, "RATELIMIT_AUTH_RATE", "10/m")
            group_prefix = "auth"
        else:
            rate_setting = getattr(settings, "RATELIMIT_GLOBAL_RATE", "100/m")
            group_prefix = "global"

        limit, period = parse_rate(rate_setting)
        limited, retry_after = is_rate_limited(group_prefix, identifier, limit, period)

        if limited:
            return build_rate_limit_response(retry_after, is_htmx=is_htmx)

        return self.get_response(request)


def ratelimit(rate: str = "10/m", group: Optional[str] = None, block: bool = True):
    """
    Decorator for views to enforce custom per-view rate limits.
    """

    def decorator(view_func: Callable):
        @functools.wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            enabled = getattr(settings, "RATELIMIT_ENABLE", True)
            if not enabled:
                return view_func(request, *args, **kwargs)

            group_prefix = group or view_func.__name__
            limit, period = parse_rate(rate)
            identifier = get_client_identifier(request)

            limited, retry_after = is_rate_limited(
                group_prefix, identifier, limit, period
            )
            if limited and block:
                is_htmx = is_htmx_request(request)
                return build_rate_limit_response(retry_after, is_htmx=is_htmx)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
