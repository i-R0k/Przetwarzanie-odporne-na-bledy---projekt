from __future__ import annotations

from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException

from vetclinic_api.cluster.config import CONFIG
from vetclinic_api.cluster.http_client import get_http_client
from vetclinic_api.cluster import faults as faults_config
from vetclinic_api.cluster.faults import apply_faults_for_rpc
from vetclinic_api.blockchain.core import (
    BlockProposal,
    Storage,
    block_header_bytes,
    compute_block_hash,
    is_valid_new_block,
)
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.crypto.ed25519 import (
    load_leader_keys_from_env,
    verify_signature,
)

router = APIRouter(prefix="/rpc", tags=["rpc"])


@router.get("/node-info")
async def node_info(_faults: None = Depends(apply_faults_for_rpc)):
    """
    Zwraca podstawowe informacje o tym węźle.
    """
    return {
        "node_id": CONFIG.node_id,
        "leader_id": CONFIG.leader_id,
        "peers": CONFIG.peers,
    }


@router.get("/leader-info")
async def leader_info(_faults: None = Depends(apply_faults_for_rpc)):
    """
    Zwraca identyfikator lidera znany temu węzłowi.
    Na Dzień 4: wszędzie ta sama wartość, z konfiguracji.
    """
    return {"leader_id": CONFIG.leader_id}


@router.get("/ping-peers")
async def ping_peers(
    client: httpx.AsyncClient = Depends(get_http_client),
    _faults: None = Depends(apply_faults_for_rpc),
):
    """
    Testowo odpytuje wszystkich peers o /rpc/node-info.
    Nie jest to mechanizm konsensusu, tylko diagnostyka sieci.
    """
    results: List[dict] = []
    for base_url in CONFIG.peers:
        url = f"{base_url.rstrip('/')}/rpc/node-info"
        try:
            resp = await client.get(url)
            ok = resp.status_code == 200
            payload = resp.json() if ok else None
            results.append(
                {
                    "url": url,
                    "ok": ok,
                    "response": payload,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "url": url,
                    "ok": False,
                    "error": str(exc),
                }
            )
    return {
        "node_id": CONFIG.node_id,
        "leader_id": CONFIG.leader_id,
        "results": results,
    }


@router.post("/propose_block")
async def propose_block(
    proposal: BlockProposal,
    storage: Storage = Depends(get_storage),
    _faults: None = Depends(apply_faults_for_rpc),
):
    chain = storage.get_chain()
    if not chain:
        raise HTTPException(status_code=500, detail="Empty chain on follower")

    last = chain[-1]

    is_ok = is_valid_new_block(last, proposal.block)

    computed_hash = compute_block_hash(proposal.block)
    if computed_hash != proposal.hash:
        is_ok = False

    keys = load_leader_keys_from_env()
    header_bytes = block_header_bytes(proposal.block)
    if not verify_signature(keys.pub, header_bytes, proposal.block.leader_sig):
        is_ok = False

    if faults_config.FAULTS.byzantine:
        if is_ok:
            return {"vote": "reject", "byzantine": True}
        return {"vote": "accept", "byzantine": True}

    return {"vote": "accept" if is_ok else "reject", "byzantine": False}


@router.post("/commit_block")
async def commit_block(
    proposal: BlockProposal,
    storage: Storage = Depends(get_storage),
    _faults: None = Depends(apply_faults_for_rpc),
):
    chain = storage.get_chain()
    if not chain:
        raise HTTPException(status_code=500, detail="Empty chain on commit")

    last = chain[-1]
    if not is_valid_new_block(last, proposal.block):
        raise HTTPException(status_code=400, detail="Invalid block on commit")

    keys = load_leader_keys_from_env()
    header_bytes = block_header_bytes(proposal.block)
    if not verify_signature(keys.pub, header_bytes, proposal.block.leader_sig):
        raise HTTPException(status_code=400, detail="Invalid leader signature")

    if faults_config.FAULTS.byzantine:
        return {"status": "committed", "byzantine": True}

    storage.add_block(proposal.block)
    return {"status": "committed", "byzantine": False}
