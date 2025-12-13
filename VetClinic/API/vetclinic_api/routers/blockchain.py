import hashlib
import json
import time
from datetime import datetime
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from vetclinic_api.blockchain.core import (
    BlockchainState,
    Storage,
    Transaction,
    TxPayload,
    build_block_proposal,
    compute_block_hash,
    mine_block,
    verify_chain,
)
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.cluster.config import CONFIG
from vetclinic_api.cluster.http_client import get_http_client
from vetclinic_api.cluster.faults import apply_faults_for_rpc
from vetclinic_api.crypto.ed25519 import (
    load_leader_keys_from_env,
    sign_message,
)
from vetclinic_api.metrics import (
    NODE_NAME,
    chain_verify_duration_seconds,
    chain_verify_total,
    inc_tx_rejected,
    inc_tx_submitted,
    set_chain_status,
)

router = APIRouter(tags=["blockchain"])


class SubmitTransaction(BaseModel):
    sender: str = Field(min_length=3, max_length=128)
    recipient: str = Field(min_length=3, max_length=128)
    amount: float = Field(gt=0, lt=1e9)

    @validator("sender", "recipient")
    def strip_and_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("value must not be empty")
        return v


@router.post("/tx/submit", status_code=202)
async def submit_transaction(
    tx: SubmitTransaction,
    storage: Storage = Depends(get_storage),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    if CONFIG.node_id != CONFIG.leader_id:
        if not CONFIG.leader_url:
            inc_tx_rejected("exception")
            raise HTTPException(status_code=500, detail="Leader URL not configured")
        try:
            resp = await client.post(
                f"{CONFIG.leader_url.rstrip('/')}/tx/submit",
                json=tx.model_dump(mode="json"),
            )
        except httpx.HTTPError as exc:
            inc_tx_rejected("exception")
            raise HTTPException(
                status_code=502,
                detail=f"Leader unreachable: {exc}",
            ) from exc

        try:
            payload = resp.json()
        except ValueError:
            payload = {"detail": resp.text}

        return JSONResponse(status_code=resp.status_code, content=payload)

    try:
        payload = TxPayload(
            sender=tx.sender,
            recipient=tx.recipient,
            amount=Decimal(str(tx.amount)),
        )
        timestamp = datetime.utcnow()
        raw = json.dumps(
            {"payload": payload.model_dump(mode="json"), "timestamp": timestamp.isoformat()},
            sort_keys=True,
        ).encode("utf-8")
        tx_id = hashlib.sha256(raw).hexdigest()

        keys = load_leader_keys_from_env()
        signature = sign_message(keys.priv, raw)

        transaction = Transaction(
            id=tx_id,
            payload=payload,
            sender_pub="demo-sender-pub",
            signature=signature,
            timestamp=timestamp,
        )
        storage.add_transaction(transaction)
    except ValueError:
        inc_tx_rejected("validation")
        raise
    except Exception:
        inc_tx_rejected("exception")
        raise

    # Broadcast transaction to peers so each keeps it in mempool.
    for base_url in CONFIG.peers:
        url = f"{base_url.rstrip('/')}/tx/receive"
        try:
            await client.post(url, json=transaction.model_dump(mode="json"))
        except Exception:
            # Best-effort: nie blokujemy lokalnej akceptacji.
            continue

    inc_tx_submitted()
    return {"status": "accepted"}


@router.get("/chain/status")
def chain_status(
    storage: Storage = Depends(get_storage),
):
    chain = storage.get_chain()
    mempool = storage.get_mempool()
    state = BlockchainState(chain=chain, mempool=mempool)

    last_block_hash = compute_block_hash(chain[-1]) if chain else None
    height = len(chain) - 1 if chain else -1
    mempool_size = len(mempool)

    set_chain_status(height=height, mempool_size=mempool_size)

    return {
        "height": height,
        "last_block_hash": last_block_hash,
        "mempool_size": mempool_size,
        "chain": state.chain,
        "mempool": state.mempool,
    }


@router.post("/tx/receive", status_code=202, include_in_schema=False)
async def receive_transaction(
    tx: Transaction,
    storage: Storage = Depends(get_storage),
):
    try:
        storage.add_transaction(tx)
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to enqueue transaction")

    return {"status": "queued"}


@router.post("/chain/mine")
def mine_block_endpoint(
    storage: Storage = Depends(get_storage),
):
    """
    Kopie nowy blok z aktualnego mempoola.
    Jesli mempool jest pusty, zwraca 400.
    """
    try:
        block = mine_block(storage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    block_hash = compute_block_hash(block)
    return {
        "status": "mined",
        "block_hash": block_hash,
        "block": block,
    }


@router.get("/chain/verify")
async def verify_chain_endpoint(
    storage: Storage = Depends(get_storage),
):
    start = time.perf_counter()
    try:
        result = verify_chain(storage)
        ok = bool(result.get("valid"))
        chain_verify_total.labels(NODE_NAME, "ok" if ok else "invalid").inc()
        return result
    except Exception:
        chain_verify_total.labels(NODE_NAME, "error").inc()
        raise
    finally:
        elapsed = time.perf_counter() - start
        chain_verify_duration_seconds.labels(NODE_NAME).observe(elapsed)


@router.post("/chain/mine_distributed")
async def mine_distributed(
    storage: Storage = Depends(get_storage),
    client: httpx.AsyncClient = Depends(get_http_client),
    _faults: None = Depends(apply_faults_for_rpc),
):
    if CONFIG.node_id != CONFIG.leader_id:
        raise HTTPException(status_code=400, detail="Not a leader")

    try:
        proposal = build_block_proposal(storage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    votes = 1
    total = 1

    payload = proposal.model_dump(mode="json")

    for base_url in CONFIG.peers:
        url = f"{base_url.rstrip('/')}/rpc/propose_block"
        total += 1
        try:
            resp = await client.post(url, json=payload)
        except Exception:
            continue
        if resp.status_code == 200:
            try:
                body = resp.json()
            except ValueError:
                continue
            if body.get("vote") == "accept":
                votes += 1

    if votes <= total // 2:
        return {"status": "rejected", "votes": votes, "total": total}

    storage.add_block(proposal.block)

    for base_url in CONFIG.peers:
        url = f"{base_url.rstrip('/')}/rpc/commit_block"
        try:
            await client.post(url, json=payload)
        except Exception:
            continue

    return {
        "status": "committed",
        "block_hash": proposal.hash,
        "votes": votes,
        "total": total,
    }
