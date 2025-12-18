from __future__ import annotations

import types

import requests

import trafficgen.trafficgen as tg


def test_get_state_returns_fallback_on_error(monkeypatch):
    def raise_exc(*_args, **_kwargs):
        raise requests.RequestException("boom")

    monkeypatch.setattr(tg.SESSION, "get", raise_exc)
    state = tg.get_state()
    assert state["traffic_enabled"] is True
    assert state["traffic_rps"] == 0.5


def test_submit_tx_handles_errors(monkeypatch):
    called = {"count": 0}

    def raise_exc(*_args, **_kwargs):
        called["count"] += 1
        raise requests.RequestException("boom")

    monkeypatch.setattr(tg.SESSION, "post", raise_exc)
    # Should not raise despite the request failing.
    tg.submit_tx()
    assert called["count"] == 1
