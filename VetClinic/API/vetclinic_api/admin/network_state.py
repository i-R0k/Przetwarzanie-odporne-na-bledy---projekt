from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class NetworkSimState:
    traffic_enabled: bool = True
    traffic_rps: float = 1.0
    chaos_enabled: bool = False
    chaos_error_rate: float = 0.02
    chaos_delay_rate: float = 0.05
    chaos_delay_ms_min: int = 50
    chaos_delay_ms_max: int = 300

    offline: bool = False
    slow_ms: int = 0
    byzantine: bool = False
    flapping: bool = False
    flapping_mod: int = 0
    drop_rpc_prob: float = 0.0

    _call_counters: Dict[str, int] = field(default_factory=dict, repr=False)
    _rng: random.Random = field(default_factory=random.Random, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def drop_rpc_probability(self) -> float:
        return self.drop_rpc_prob

    @drop_rpc_probability.setter
    def drop_rpc_probability(self, value: float) -> None:
        self.drop_rpc_prob = max(0.0, min(1.0, float(value)))

    def next_call_index(self, endpoint: str) -> int:
        with self._lock:
            self._call_counters[endpoint] = self._call_counters.get(endpoint, 0) + 1
            return self._call_counters[endpoint]

    def should_drop(self) -> bool:
        p = float(self.drop_rpc_prob or 0.0)
        if p <= 0.0:
            return False
        if p >= 1.0:
            return True
        with self._lock:
            return self._rng.random() < p

    def reset_counters(self) -> None:
        with self._lock:
            self._call_counters.clear()


STATE = NetworkSimState()


def get_state() -> NetworkSimState:
    return STATE


def update_state(**kwargs) -> NetworkSimState:
    state = STATE
    with state._lock:
        for key, value in kwargs.items():
            if hasattr(state, key) and not key.startswith("_"):
                setattr(state, key, value)
    return state


def state_payload() -> dict:
    payload = {
        key: value
        for key, value in STATE.__dict__.items()
        if not key.startswith("_")
    }
    payload["drop_rpc_probability"] = STATE.drop_rpc_probability
    return payload
