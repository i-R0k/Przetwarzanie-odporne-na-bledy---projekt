from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
import httpx

from vetclinic_api.cluster.config import CONFIG
from vetclinic_api.cluster.http_client import get_http_client

router = APIRouter(prefix="/rpc", tags=["rpc"])


@router.get("/node-info")
async def node_info():
    """
    Zwraca podstawowe informacje o tym węźle.
    """
    return {
        "node_id": CONFIG.node_id,
        "leader_id": CONFIG.leader_id,
        "peers": CONFIG.peers,
    }


@router.get("/leader-info")
async def leader_info():
    """
    Zwraca identyfikator lidera znany temu węzłowi.
    Na Dzień 4: wszędzie ta sama wartość, z konfiguracji.
    """
    return {"leader_id": CONFIG.leader_id}


@router.get("/ping-peers")
async def ping_peers(
    client: httpx.AsyncClient = Depends(get_http_client),
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
