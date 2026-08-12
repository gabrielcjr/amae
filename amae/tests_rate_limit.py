import pytest
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from django.urls import reverse

from amae.middleware.rate_limit import (
    get_client_ip,
    is_rate_limited,
    parse_rate,
    ratelimit,
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_parse_rate():
    assert parse_rate("100/m") == (100, 60)
    assert parse_rate("10/s") == (10, 1)
    assert parse_rate("500/h") == (500, 3600)
    assert parse_rate("1000/d") == (1000, 86400)
    assert parse_rate("invalid") == (100, 60)
    assert parse_rate("") == (100, 60)


def test_get_client_ip():
    factory = RequestFactory()

    req1 = factory.get("/", REMOTE_ADDR="192.168.1.1")
    assert get_client_ip(req1) == "192.168.1.1"

    req2 = factory.get("/", HTTP_X_FORWARDED_FOR="203.0.113.195, 70.41.3.18")
    assert get_client_ip(req2) == "203.0.113.195"


def test_is_rate_limited():
    key_prefix = "test_func"
    identifier = "127.0.0.1"
    limit = 3
    period = 10

    limited, _ = is_rate_limited(key_prefix, identifier, limit, period)
    assert not limited

    limited, _ = is_rate_limited(key_prefix, identifier, limit, period)
    assert not limited

    limited, _ = is_rate_limited(key_prefix, identifier, limit, period)
    assert not limited

    # 4th request exceeds limit of 3
    limited, retry_after = is_rate_limited(key_prefix, identifier, limit, period)
    assert limited
    assert retry_after > 0


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True, RATELIMIT_GLOBAL_RATE="3/m")
def test_global_rate_limit_middleware(client):
    url = reverse("home")

    # 3 allowed requests
    for _ in range(3):
        response = client.get(url)
        assert response.status_code == 200

    # 4th request rate limited
    response = client.get(url)
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert "Muitas requisições" in response.content.decode("utf-8")


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True, RATELIMIT_AUTH_RATE="2/m")
def test_auth_rate_limit_middleware(client):
    url = reverse("login")

    # 2 allowed requests
    for _ in range(2):
        response = client.get(url)
        assert response.status_code == 200

    # 3rd request rate limited on auth endpoint
    response = client.get(url)
    assert response.status_code == 429
    assert "Retry-After" in response.headers


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=True, RATELIMIT_GLOBAL_RATE="1/m")
def test_htmx_rate_limit_response(client):
    url = reverse("home")

    # Request 1
    client.get(url)

    # Request 2 with HTMX header
    response = client.get(url, HTTP_HX_REQUEST="true")
    assert response.status_code == 429
    assert response.headers["Content-Type"].startswith("text/html")
    assert "<div class='p-4 bg-red-100" in response.content.decode("utf-8")


@pytest.mark.django_db
@override_settings(RATELIMIT_ENABLE=False, RATELIMIT_GLOBAL_RATE="1/m")
def test_rate_limit_disabled(client):
    url = reverse("home")

    for _ in range(5):
        response = client.get(url)
        assert response.status_code == 200


def test_ratelimit_decorator():
    factory = RequestFactory()

    @ratelimit(rate="2/m", group="decorator_test")
    def sample_view(request):
        from django.http import HttpResponse

        return HttpResponse("OK")

    req = factory.get("/")
    assert sample_view(req).status_code == 200
    assert sample_view(req).status_code == 200

    res_blocked = sample_view(req)
    assert res_blocked.status_code == 429
    assert "Retry-After" in res_blocked.headers
