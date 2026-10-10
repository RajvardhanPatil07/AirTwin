"""Resilient live-provider HTTP behavior: offline network-failure regression tests."""
from __future__ import annotations

import requests
import pytest

from app.services import state_data


class FakeResponse:
    def __init__(self, status, payload=None, headers=None):
        self.status_code = status
        self.payload = payload or {"ok": True}
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


def test_tls_reset_then_recovers_with_bounded_retry(monkeypatch):
    calls, delays = [], []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        if len(calls) <= 2:
            raise requests.ConnectionError("connection reset during TLS handshake")
        return FakeResponse(200, {"results": ["observed"]})

    monkeypatch.setattr(state_data.requests, "get", fake_get)
    monkeypatch.setattr(state_data.time, "sleep", delays.append)
    result = state_data.get_payload("https://air-quality-api.open-meteo.com/test",
                                    {"x": 3}, {"Accept": "application/json"})
    assert result == {"results": ["observed"]}
    assert len(calls) == 3 and delays == [1, 2]
    assert calls[0][1]["timeout"] == (10, 30)
    assert calls[0][1]["params"] == {"x": 3}


def test_http_503_and_rate_limit_use_bounded_retry_after(monkeypatch):
    responses = [
        FakeResponse(503, headers={"Retry-After": "0"}),
        FakeResponse(429, headers={"Retry-After": "9999"}),
        FakeResponse(200, {"points": []}),
    ]
    delays = []
    monkeypatch.setattr(state_data.requests, "get", lambda *_a, **_kw: responses.pop(0))
    monkeypatch.setattr(state_data.time, "sleep", delays.append)
    assert state_data.get_payload("https://api.open-meteo.com/test") == {"points": []}
    assert delays == [0.0, 30]


def test_non_retryable_http_401_fails_immediately(monkeypatch):
    calls, delays = [], []

    def fake_get(*args, **kwargs):
        calls.append(1)
        return FakeResponse(401)

    monkeypatch.setattr(state_data.requests, "get", fake_get)
    monkeypatch.setattr(state_data.time, "sleep", delays.append)
    with pytest.raises(requests.HTTPError, match="401"):
        state_data.get_payload("https://api.openaq.org/test")
    assert len(calls) == 1
    assert delays == []


def test_persistent_connection_reset_keeps_failure_visible(monkeypatch):
    calls, delays = [], []

    def fake_get(*_args, **_kwargs):
        calls.append(1)
        raise requests.ConnectionError("WinError 10054")

    monkeypatch.setattr(state_data.requests, "get", fake_get)
    monkeypatch.setattr(state_data.time, "sleep", delays.append)
    with pytest.raises(requests.ConnectionError, match="10054"):
        state_data.get_payload("https://api.open-meteo.com/test")
    assert len(calls) == 4
    assert delays == [1, 2, 4]


def test_http_500_retry_exhaustion_raises(monkeypatch):
    calls, delays = [], []

    def fake_get(*_args, **_kwargs):
        calls.append(1)
        return FakeResponse(500)

    monkeypatch.setattr(state_data.requests, "get", fake_get)
    monkeypatch.setattr(state_data.time, "sleep", delays.append)
    with pytest.raises(requests.HTTPError, match="500"):
        state_data.get_payload("https://api.open-meteo.com/test")
    assert len(calls) == 4
    assert delays == [1.0, 2.0, 4.0]
