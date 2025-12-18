from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vetclinic_api.admin.network_state import STATE
from vetclinic_api.middleware.chaos import ChaosMiddleware


def test_chaos_middleware_injects_error(monkeypatch):
    # Force chaos to be enabled and always trigger delay + error.
    STATE.chaos_enabled = True
    STATE.chaos_delay_rate = 1.0
    STATE.chaos_error_rate = 1.0
    STATE.chaos_delay_ms_min = 0
    STATE.chaos_delay_ms_max = 0

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("vetclinic_api.middleware.chaos.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("vetclinic_api.middleware.chaos.random.random", lambda: 0.0)

    app = FastAPI()
    app.add_middleware(ChaosMiddleware)

    @app.get("/chain/test")
    def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/chain/test")
    assert resp.status_code == 500
    assert resp.json()["detail"] == "simulated_failure"


def test_chaos_middleware_allows_other_paths(monkeypatch):
    STATE.chaos_enabled = True
    STATE.chaos_delay_rate = 0.0
    STATE.chaos_error_rate = 1.0
    monkeypatch.setattr("vetclinic_api.middleware.chaos.random.random", lambda: 1.0)

    app = FastAPI()
    app.add_middleware(ChaosMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
