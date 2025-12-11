from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

API_BASE = "http://localhost:8000"


def _url(path: str) -> str:
    return API_BASE.rstrip("/") + path


def add_record_on_chain(record_id: int, data_hash: str, owner: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"id": record_id, "data_hash": data_hash}
    if owner is not None:
        payload["owner"] = owner
    resp = requests.post(_url("/blockchain/record"), json=payload, timeout=5.0)
    resp.raise_for_status()
    return resp.json()


def get_record_on_chain(record_id: int) -> Optional[Dict[str, Any]]:
    resp = requests.get(_url(f"/blockchain/record/{record_id}"), timeout=5.0)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_records_by_owner(owner: str) -> List[int]:
    resp = requests.get(_url(f"/blockchain/records-by-owner/{owner}"), timeout=5.0)
    resp.raise_for_status()
    data = resp.json()
    return list(data.get("record_ids", []))
