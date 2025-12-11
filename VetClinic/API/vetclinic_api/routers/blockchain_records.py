from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from vetclinic_api.blockchain.core import (
    Transaction,
    TxPayload,
)
from vetclinic_api.blockchain.deps import get_storage, Storage
from vetclinic_api.crypto.ed25519 import load_leader_keys_from_env, sign_message

router = APIRouter(prefix="/blockchain", tags=["blockchain-compat"])


class BlockchainRecord(BaseModel):
    id: int
    data_hash: str
    owner: Optional[str] = None


def _build_record_tx(record: BlockchainRecord) -> Transaction:
    payload = TxPayload(
        kind="MEDICAL_RECORD",
        record_id=record.id,
        data_hash=record.data_hash,
        owner=record.owner or "system",
    )
    ts = datetime.utcnow()
    raw = json.dumps(
        {"payload": payload.model_dump(mode="json"), "timestamp": ts.isoformat()},
        sort_keys=True,
    ).encode("utf-8")
    tx_id = hashlib.sha256(raw).hexdigest()

    keys = load_leader_keys_from_env()
    signature = sign_message(keys.priv, raw)

    return Transaction(
        id=tx_id,
        payload=payload,
        sender_pub="leader-demo",
        signature=signature,
        timestamp=ts,
    )


def _iter_record_txs(chain) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for block in chain:
        for tx in block.transactions:
            payload = tx.payload
            if getattr(payload, "kind", None) != "MEDICAL_RECORD":
                continue
            results.append(
                {
                    "record_id": getattr(payload, "record_id", None),
                    "data_hash": getattr(payload, "data_hash", None),
                    "owner": getattr(payload, "owner", None),
                    "timestamp": tx.timestamp,
                    "block_index": block.index,
                    "tx_id": tx.id,
                }
            )
    return results


@router.post("/record")
def add_blockchain_record(
    record: BlockchainRecord, storage: Storage = Depends(get_storage)
):
    tx = _build_record_tx(record)
    storage.add_transaction(tx)
    return {"status": "ok", "tx_id": tx.id}


@router.get("/record/{record_id}")
def get_blockchain_record(
    record_id: int, storage: Storage = Depends(get_storage)
):
    chain = storage.get_chain()
    records = [
        tx for tx in _iter_record_txs(chain) if tx["record_id"] == record_id
    ]
    if not records:
        raise HTTPException(status_code=404, detail="Record not found on-chain")
    latest = sorted(records, key=lambda item: item["timestamp"])[-1]
    return {
        "id": latest["record_id"],
        "data_hash": latest["data_hash"],
        "timestamp": latest["timestamp"],
        "owner": latest["owner"],
        "block_index": latest["block_index"],
        "tx_id": latest["tx_id"],
    }


@router.get("/records-by-owner/{owner}")
def get_records_by_owner(owner: str, storage: Storage = Depends(get_storage)):
    chain = storage.get_chain()
    records = _iter_record_txs(chain)
    ids = sorted({tx["record_id"] for tx in records if tx["owner"] == owner})
    return {"owner": owner, "record_ids": ids}
