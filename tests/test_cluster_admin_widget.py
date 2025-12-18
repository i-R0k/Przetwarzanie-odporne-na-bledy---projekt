from __future__ import annotations

import json
from typing import Any, Dict

import pytest
from PyQt5.QtWidgets import QApplication

from VetClinic.GUI.vetclinic_gui.windows.Admin import cluster_admin_widget as widget_module


class _Resp:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    @property
    def text(self):
        return json.dumps(self._payload)

    def raise_for_status(self):
        if not (200 <= self.status_code < 400):
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def stub_requests(monkeypatch):
    sent = {}

    def fake_get(url, timeout=3.0):
        if "/chain/status" in url:
            return _Resp(
                {
                    "height": 1,
                    "last_block_hash": "abcd" * 16,
                    "mempool_size": 0,
                    "chain": [],
                    "mempool": [],
                }
            )
        if "/chain/verify" in url:
            return _Resp({"valid": True, "errors": []})
        if "/admin/network/sim" in url:
            return _Resp(
                {
                    "traffic_enabled": True,
                    "traffic_rps": 1.0,
                    "chaos_enabled": False,
                    "chaos_error_rate": 0.02,
                    "chaos_delay_rate": 0.05,
                    "chaos_delay_ms_min": 50,
                    "chaos_delay_ms_max": 300,
                }
            )
        return _Resp({})

    def fake_put(url, json=None, timeout=5.0):
        sent["url"] = url
        sent["json"] = json
        return _Resp(json or {}, 200)

    monkeypatch.setattr(widget_module.requests, "get", fake_get)
    monkeypatch.setattr(widget_module.requests, "put", fake_put)
    return sent


def test_cluster_admin_toggle_traffic(stub_requests):
    app = QApplication.instance() or QApplication([])
    w = widget_module.ClusterAdminWidget()

    assert w.chk_traffic.isChecked() is True
    # Toggle off -> should send payload with traffic_enabled False
    w.chk_traffic.setChecked(False)
    assert stub_requests["json"]["traffic_enabled"] is False
    w.close()
