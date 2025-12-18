from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from vetclinic_api.admin.network_state import NetworkSimState, STATE, update_state
from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    Transaction,
    TxPayload,
    build_block_proposal,
)
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.crypto.ed25519 import (
    generate_keypair,
    load_leader_keys_from_env,
    sign_message,
)
from vetclinic_api.main import app


def _make_transaction() -> Transaction:
    payload = TxPayload(
        sender="alice",
        recipient="bob",
        amount=Decimal("1.0"),
    )
    timestamp = datetime.utcnow()
    raw = json.dumps(
        {"payload": payload.model_dump(mode="json"), "timestamp": timestamp.isoformat()},
        sort_keys=True,
    ).encode("utf-8")
    tx_id = hashlib.sha256(raw).hexdigest()
    keys = load_leader_keys_from_env()
    signature = sign_message(keys.priv, raw)
    return Transaction(
        id=tx_id,
        payload=payload,
        sender_pub="test-sender",
        signature=signature,
        timestamp=timestamp,
    )


def _make_valid_proposal(storage: InMemoryStorage):
    storage.clear_mempool()
    storage.add_transaction(_make_transaction())
    return build_block_proposal(storage)


def _reset_network_state() -> None:
    defaults = NetworkSimState()
    payload = {
        key: value
        for key, value in defaults.__dict__.items()
        if not key.startswith("_")
    }
    payload["drop_rpc_probability"] = defaults.drop_rpc_probability
    update_state(**payload)
    STATE.reset_counters()


@pytest.fixture(autouse=True)
def leader_keys_env(monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
    yield


@pytest.fixture(autouse=True)
def reset_state():
    _reset_network_state()
    yield
    _reset_network_state()


@pytest.fixture
def storage():
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        yield storage
    finally:
        app.dependency_overrides.pop(get_storage, None)


@pytest.fixture
def client(storage):
    with TestClient(app) as test_client:
        yield test_client


def test_propose_block_offline_returns_503(client: TestClient, storage):
    update_state(offline=True)
    proposal = _make_valid_proposal(storage)
    response = client.post(
        "/rpc/propose_block",
        json=proposal.model_dump(mode="json"),
    )
    assert response.status_code == 503


def test_commit_block_offline_returns_503(client: TestClient, storage):
    update_state(offline=True)
    proposal = _make_valid_proposal(storage)
    response = client.post(
        "/rpc/commit_block",
        json=proposal.model_dump(mode="json"),
    )
    assert response.status_code == 503


def test_propose_block_byzantine_inverts_vote(client: TestClient, storage):
    update_state(byzantine=True)
    proposal = _make_valid_proposal(storage)
    response = client.post(
        "/rpc/propose_block",
        json=proposal.model_dump(mode="json"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["vote"] == "reject"
    assert body["byzantine"] is True


def test_commit_block_byzantine_does_not_change_height(client: TestClient, storage):
    update_state(byzantine=True)
    proposal = _make_valid_proposal(storage)
    height_before = client.get("/chain/status").json()["height"]
    response = client.post(
        "/rpc/commit_block",
        json=proposal.model_dump(mode="json"),
    )
    height_after = client.get("/chain/status").json()["height"]
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "committed"
    assert body["byzantine"] is True
    assert height_after == height_before


def test_mine_distributed_offline_returns_503(client: TestClient, storage):
    update_state(offline=True)
    storage.add_transaction(_make_transaction())
    response = client.post("/chain/mine_distributed")
    assert response.status_code == 503


def test_propose_block_flapping_blocks_every_other_call(client: TestClient, storage):
    update_state(flapping=True, flapping_mod=2)
    STATE.reset_counters()
    proposal = _make_valid_proposal(storage)
    resp1 = client.post("/rpc/propose_block", json=proposal.model_dump(mode="json"))
    assert resp1.status_code == 503
    resp2 = client.post("/rpc/propose_block", json=proposal.model_dump(mode="json"))
    assert resp2.status_code == 200


def test_propose_block_drop_rpc_probability(client: TestClient, storage):
    update_state(drop_rpc_probability=1.0)
    proposal = _make_valid_proposal(storage)
    resp = client.post("/rpc/propose_block", json=proposal.model_dump(mode="json"))
    assert resp.status_code == 503
