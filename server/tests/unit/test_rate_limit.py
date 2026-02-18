"""Unit tests for rate limit middleware."""

from unittest.mock import MagicMock

import pytest

from app.core.rate_limit import RateLimitMiddleware, _get_client_ip


def test_get_client_ip_from_forwarded():
    request = MagicMock()
    request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
    request.client = None
    assert _get_client_ip(request) == "192.168.1.1"


def test_get_client_ip_from_client():
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock(host="127.0.0.1")
    assert _get_client_ip(request) == "127.0.0.1"


@pytest.mark.asyncio
async def test_rate_limit_allows_under_limit(monkeypatch):
    from app.core.rate_limit import _rate
    _rate.clear()
    monkeypatch.setattr("app.core.rate_limit.settings.rate_limit_per_minute_per_ip", 2)
    from starlette.requests import Request
    from starlette.responses import Response

    middleware = RateLimitMiddleware(app=MagicMock())
    call_count = 0

    async def next_handler(request: Request):
        nonlocal call_count
        call_count += 1
        return Response("ok")

    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = MagicMock(host="1.2.3.4")
    for _ in range(2):
        resp = await middleware.dispatch(request, next_handler)
        assert resp.status_code == 200
    assert call_count == 2
    _rate.clear()


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(monkeypatch):
    from app.core.rate_limit import _rate
    _rate.clear()
    monkeypatch.setattr("app.core.rate_limit.settings.rate_limit_per_minute_per_ip", 1)
    from starlette.requests import Request
    from starlette.responses import Response

    middleware = RateLimitMiddleware(app=MagicMock())

    async def next_handler(request: Request):
        return Response("ok")

    request = MagicMock(spec=Request)
    request.headers = {}
    request.client = MagicMock(host="5.6.7.8")
    r1 = await middleware.dispatch(request, next_handler)
    r2 = await middleware.dispatch(request, next_handler)
    assert r1.status_code == 200
    assert r2.status_code == 429
    _rate.clear()
