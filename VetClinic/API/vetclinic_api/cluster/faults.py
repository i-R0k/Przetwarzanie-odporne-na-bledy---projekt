from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class FaultConfig:
    offline: bool = False  # FAULT_OFFLINE
    slow_ms: int = 0  # FAULT_SLOW_MS
    byzantine: bool = False  # FAULT_BYZANTINE

    flapping: bool = False  # FAULT_FLAPPING
    flapping_mod: int = 0  # FAULT_FLAPPING_MOD

    drop_rpc_prob: float = 0.0  # FAULT_DROP_RPC_PROB


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str, default: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def load_fault_config() -> FaultConfig:
    return FaultConfig(
        offline=_env_bool("FAULT_OFFLINE", False),
        slow_ms=max(_env_int("FAULT_SLOW_MS", 0), 0),
        byzantine=_env_bool("FAULT_BYZANTINE", False),
        flapping=_env_bool("FAULT_FLAPPING", False),
        flapping_mod=max(_env_int("FAULT_FLAPPING_MOD", 0), 0),
        drop_rpc_prob=max(min(_env_float("FAULT_DROP_RPC_PROB", 0.0), 1.0), 0.0),
    )


FAULTS = load_fault_config()
_RPC_CALL_COUNTER = 0


def _next_rpc_call_index() -> int:
    global _RPC_CALL_COUNTER
    _RPC_CALL_COUNTER += 1
    return _RPC_CALL_COUNTER


async def apply_faults_for_rpc() -> None:
    """
    Applies configured fault injection rules before handling consensus/RPC calls.
    Order:
    1) OFFLINE (hard fail)
    2) FLAPPING (periodic fail)
    3) SLOW (delay)
    4) DROP_RPC_PROB (random transient fail)
    """

    if FAULTS.offline:
        raise HTTPException(status_code=503, detail="Node is offline (FAULT_OFFLINE)")

    if FAULTS.flapping and FAULTS.flapping_mod > 0:
        idx = _next_rpc_call_index()
        if idx % FAULTS.flapping_mod != 0:
            raise HTTPException(
                status_code=503,
                detail="Node is temporarily unavailable (FAULT_FLAPPING)",
            )

    if FAULTS.slow_ms > 0:
        await asyncio.sleep(FAULTS.slow_ms / 1000.0)

    if FAULTS.drop_rpc_prob > 0.0:
        if random.random() < FAULTS.drop_rpc_prob:
            raise HTTPException(
                status_code=503,
                detail="Transient RPC drop (FAULT_DROP_RPC)",
            )


__all__ = [
    "FaultConfig",
    "FAULTS",
    "load_fault_config",
    "apply_faults_for_rpc",
]
