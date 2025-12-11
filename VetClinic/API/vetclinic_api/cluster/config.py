from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse


@dataclass
class NodeConfig:
    node_id: int
    leader_id: int
    peers: List[str]
    leader_url: str


def _parse_peers(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _resolve_leader_url(node_id: int, leader_id: int, peers: list[str]) -> str:
    leader_url = os.getenv("LEADER_URL")
    if leader_url:
        return leader_url

    if node_id == leader_id:
        return "http://127.0.0.1:8000"

    leader_host = f"node{leader_id}".lower()
    for peer in peers:
        try:
            parsed = urlparse(peer)
        except Exception:
            continue
        host = (parsed.hostname or "").lower()
        if host == leader_host:
            return peer

    return ""


def load_config() -> NodeConfig:
    node_id = int(os.getenv("NODE_ID", "1"))
    leader_id = int(os.getenv("LEADER_ID", "1"))
    peers = _parse_peers(os.getenv("PEERS"))
    leader_url = _resolve_leader_url(node_id, leader_id, peers)
    return NodeConfig(
        node_id=node_id,
        leader_id=leader_id,
        peers=peers,
        leader_url=leader_url,
    )


CONFIG = load_config()
