from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass
class NodeConfig:
    node_id: int
    leader_id: int
    peers: List[str]


def _parse_peers(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def load_config() -> NodeConfig:
    node_id = int(os.getenv("NODE_ID", "1"))
    leader_id = int(os.getenv("LEADER_ID", "1"))
    peers = _parse_peers(os.getenv("PEERS"))
    return NodeConfig(node_id=node_id, leader_id=leader_id, peers=peers)


CONFIG = load_config()
