from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from vetclinic_api.admin.network_state import state_payload, update_state

router = APIRouter(prefix="/admin/network", tags=["admin-network"])

SIM_FIELDS = [
    "traffic_enabled",
    "traffic_rps",
    "chaos_enabled",
    "chaos_error_rate",
    "chaos_delay_rate",
    "chaos_delay_ms_min",
    "chaos_delay_ms_max",
]

FAULT_FIELDS = [
    "offline",
    "slow_ms",
    "byzantine",
    "flapping",
    "flapping_mod",
    "drop_rpc_prob",
    "drop_rpc_probability",
]


def _select_payload(fields: list[str]) -> Dict[str, Any]:
    data = state_payload()
    return {field: data[field] for field in fields}


class NetworkSimPayload(BaseModel):
    traffic_enabled: bool
    traffic_rps: float
    chaos_enabled: bool
    chaos_error_rate: float
    chaos_delay_rate: float
    chaos_delay_ms_min: int
    chaos_delay_ms_max: int


class NetworkSimUpdate(BaseModel):
    traffic_enabled: bool | None = None
    traffic_rps: float | None = None
    chaos_enabled: bool | None = None
    chaos_error_rate: float | None = None
    chaos_delay_rate: float | None = None
    chaos_delay_ms_min: int | None = None
    chaos_delay_ms_max: int | None = None


class RpcFaultsPayload(BaseModel):
    offline: bool
    slow_ms: int
    byzantine: bool
    flapping: bool
    flapping_mod: int
    drop_rpc_prob: float
    drop_rpc_probability: float


class RpcFaultsUpdate(BaseModel):
    offline: bool | None = None
    slow_ms: int | None = Field(default=None, ge=0)
    byzantine: bool | None = None
    flapping: bool | None = None
    flapping_mod: int | None = Field(default=None, ge=0)
    drop_rpc_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    drop_rpc_probability: float | None = Field(default=None, ge=0.0, le=1.0)


@router.get("/sim", response_model=NetworkSimPayload)
def get_sim_state():
    return NetworkSimPayload(**_select_payload(SIM_FIELDS))


@router.put("/sim", response_model=NetworkSimPayload)
def set_sim_state(payload: NetworkSimUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        update_state(**updates)
    return NetworkSimPayload(**_select_payload(SIM_FIELDS))


@router.get("/state", response_model=RpcFaultsPayload)
def get_fault_state():
    return RpcFaultsPayload(**_select_payload(FAULT_FIELDS))


@router.put("/state", response_model=RpcFaultsPayload)
def set_fault_state(payload: RpcFaultsUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        update_state(**updates)
    return RpcFaultsPayload(**_select_payload(FAULT_FIELDS))
