from fastapi.testclient import TestClient

from vetclinic_api.core.database import SessionLocal
from vetclinic_api.main import app
from vetclinic_api.models_blockchain import BlockDB, TransactionDB
import vetclinic_api.blockchain.deps as deps
from vetclinic_api.blockchain.core import SQLAlchemyStorage


def _reset_chain_state():
    db = SessionLocal()
    db.query(TransactionDB).delete()
    db.query(BlockDB).delete()
    db.commit()
    db.close()
    deps._storage = SQLAlchemyStorage()


def _client():
    return TestClient(app)


def test_submit_and_mine_flow():
    _reset_chain_state()
    client = _client()
    tx = {"sender": "alice", "recipient": "bob", "amount": 10.5}
    r1 = client.post("/tx/submit", json=tx)
    assert r1.status_code == 202

    r2 = client.get("/chain/status")
    assert r2.status_code == 200
    assert r2.json()["mempool_size"] >= 1

    r3 = client.post("/chain/mine")
    assert r3.status_code == 200
    data = r3.json()
    assert data["status"] == "mined"
    assert isinstance(data["block_hash"], str)

    r4 = client.get("/chain/status")
    assert r4.status_code == 200
    assert r4.json()["mempool_size"] == 0
