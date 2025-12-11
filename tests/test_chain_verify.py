from __future__ import annotations

import random

from fastapi.testclient import TestClient

from vetclinic_api.main import app
from vetclinic_api.blockchain.core import InMemoryStorage
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.crypto.ed25519 import generate_keypair


def test_chain_verify_detects_tampered_previous_hash(monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)

    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage

    client = TestClient(app)
    payload = {"sender": "alice", "recipient": "bob", "amount": 1}
    client.post("/tx/submit", json=payload)
    client.post("/chain/mine")

    client.post("/tx/submit", json=payload)
    client.post("/chain/mine")

    assert len(storage.get_chain()) >= 2
    tampered = storage._chain[1]
    tampered.previous_hash = f"tampered-{random.randint(1, 1_000_000)}"

    storage._chain[1] = tampered

    verify_resp = client.get("/chain/verify")
    data = verify_resp.json()
    assert data["valid"] is False
    reasons = [err["reason"] for err in data["errors"]]
    assert "previous_hash mismatch" in reasons

    app.dependency_overrides.pop(get_storage, None)
