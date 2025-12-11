from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from vetclinic_api.main import app
from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    Transaction,
    TxPayload,
    build_block_proposal,
)
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.cluster import faults as faults_module
from vetclinic_api.cluster.faults import FaultConfig
from vetclinic_api.crypto.ed25519 import (
    generate_keypair,
    load_leader_keys_from_env,
    sign_message,
)


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


@pytest.fixture(autouse=True)
def leader_keys_env(monkeypatch):
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
    yield


@pytest.fixture
def set_faults(monkeypatch):
    def _set(**kwargs):
        data = {"offline": False, "slow_ms": 0, "byzantine": False}
        data.update(kwargs)
        config = FaultConfig(**data)
        monkeypatch.setattr(faults_module, "FAULTS", config)
        return config

    return _set


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


def test_propose_block_offline_returns_503(client: TestClient, storage, set_faults):
    set_faults(offline=True)
    proposal = _make_valid_proposal(storage)
    response = client.post(
        "/rpc/propose_block",
        json=proposal.model_dump(mode="json"),
    )
    assert response.status_code == 503


def test_commit_block_offline_returns_503(client: TestClient, storage, set_faults):
    set_faults(offline=True)
    proposal = _make_valid_proposal(storage)
    response = client.post(
        "/rpc/commit_block",
        json=proposal.model_dump(mode="json"),
    )
    assert response.status_code == 503


def test_propose_block_byzantine_inverts_vote(client: TestClient, storage, set_faults):
    set_faults(byzantine=True)
    proposal = _make_valid_proposal(storage)
    response = client.post(
        "/rpc/propose_block",
        json=proposal.model_dump(mode="json"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["vote"] == "reject"
    assert body["byzantine"] is True


def test_commit_block_byzantine_does_not_change_height(
    client: TestClient, storage, set_faults
):
    set_faults(byzantine=True)
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


def test_mine_distributed_offline_returns_503(
    client: TestClient, storage, set_faults
):
    set_faults(offline=True)
    storage.add_transaction(_make_transaction())
    response = client.post("/chain/mine_distributed")
    assert response.status_code == 503


def test_propose_block_flapping_blocks_every_other_call(
    client: TestClient, storage, set_faults, monkeypatch
):
    set_faults(flapping=True, flapping_mod=2)
    monkeypatch.setattr(faults_module, "_RPC_CALL_COUNTER", 0)
    proposal = _make_valid_proposal(storage)
    resp1 = client.post("/rpc/propose_block", json=proposal.model_dump(mode="json"))
    assert resp1.status_code == 503
    resp2 = client.post("/rpc/propose_block", json=proposal.model_dump(mode="json"))
    assert resp2.status_code == 200


def test_propose_block_drop_rpc_probability(
    client: TestClient, storage, set_faults, monkeypatch
):
    set_faults(drop_rpc_prob=1.0)
    monkeypatch.setattr(faults_module, "_RPC_CALL_COUNTER", 0)
    monkeypatch.setattr("vetclinic_api.cluster.faults.random.random", lambda: 0.0)
    proposal = _make_valid_proposal(storage)
    resp = client.post("/rpc/propose_block", json=proposal.model_dump(mode="json"))
    assert resp.status_code == 503
