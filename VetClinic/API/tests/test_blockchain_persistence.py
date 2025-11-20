from fastapi.testclient import TestClient

import vetclinic_api.blockchain.deps as deps
from vetclinic_api.blockchain.core import SQLAlchemyStorage
from vetclinic_api.core.database import SessionLocal
from vetclinic_api.main import app
from vetclinic_api.models_blockchain import BlockDB, TransactionDB


def _reset_chain_state():
    db = SessionLocal()
    db.query(TransactionDB).delete()
    db.query(BlockDB).delete()
    db.commit()
    db.close()
    deps._storage = SQLAlchemyStorage()


def test_chain_persists_between_restarts():
    _reset_chain_state()
    client = TestClient(app)

    tx = {"sender": "alice", "recipient": "bob", "amount": 5.0}
    r_submit = client.post("/tx/submit", json=tx)
    assert r_submit.status_code == 202

    r_mine = client.post("/chain/mine")
    assert r_mine.status_code == 200

    status_1 = client.get("/chain/status").json()
    assert status_1["height"] >= 1
    assert status_1["mempool_size"] == 0
    assert len(status_1["chain"]) == status_1["height"] + 1

    # simulate restart: new storage + new client
    deps._storage = SQLAlchemyStorage()
    client2 = TestClient(app)
    status_2 = client2.get("/chain/status").json()

    assert status_2["height"] == status_1["height"]
    assert status_2["mempool_size"] == 0
    assert len(status_2["chain"]) == len(status_1["chain"])
    assert status_2["chain"][-1]["transactions"]
    assert status_2["chain"][-1]["transactions"][0]["sender"] == "alice"
