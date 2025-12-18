from __future__ import annotations

from fastapi.testclient import TestClient

from vetclinic_api.admin.network_state import NetworkSimState, STATE, update_state
from vetclinic_api.main import app


def _reset_state() -> None:
    defaults = NetworkSimState()
    payload = {
        key: value
        for key, value in defaults.__dict__.items()
        if not key.startswith("_")
    }
    payload["drop_rpc_probability"] = defaults.drop_rpc_probability
    update_state(**payload)


def test_get_sim_state_returns_defaults():
    _reset_state()
    client = TestClient(app)
    resp = client.get("/admin/network/sim")
    assert resp.status_code == 200
    data = resp.json()
    assert data["traffic_enabled"] is True
    assert data["traffic_rps"] == 1.0
    assert data["chaos_enabled"] is False


def test_put_sim_state_updates_state():
    _reset_state()
    client = TestClient(app)
    payload = {
        "traffic_enabled": False,
        "traffic_rps": 2.5,
        "chaos_enabled": True,
        "chaos_error_rate": 0.1,
        "chaos_delay_rate": 0.2,
        "chaos_delay_ms_min": 10,
        "chaos_delay_ms_max": 20,
    }
    resp = client.put("/admin/network/sim", json=payload)
    assert resp.status_code == 200
    returned = resp.json()
    assert returned["traffic_enabled"] is False
    assert returned["traffic_rps"] == 2.5
    # verify STATE mutated in-place
    assert STATE.chaos_enabled is True
    assert STATE.chaos_error_rate == 0.1
