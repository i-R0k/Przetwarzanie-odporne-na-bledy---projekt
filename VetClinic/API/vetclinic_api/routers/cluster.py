from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends

from vetclinic_api.cluster.config import CONFIG
from vetclinic_api.cluster.http_client import get_http_client

router = APIRouter(prefix="/peers", tags=["cluster"])


@router.get("")
async def list_peers(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> Dict[str, Any]:
    """
    Publiczny widok klastra z punktu widzenia aktualnego węzła.
    Lista peerów wraz z wynikiem pingowania /rpc/node-info.
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
                    "url": base_url,
                    "ok": ok,
                    "node_info": payload,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "url": base_url,
                    "ok": False,
                    "error": str(exc),
                }
            )

    return {
        "self": {
            "node_id": CONFIG.node_id,
            "leader_id": CONFIG.leader_id,
            "is_leader": CONFIG.node_id == CONFIG.leader_id,
        },
        "peers": results,
    }
