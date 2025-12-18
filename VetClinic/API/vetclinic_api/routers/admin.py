from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from vetclinic_api.admin.network_state import state_payload, update_state

router = APIRouter(prefix="/admin", tags=["admin"])

FAULT_FIELDS = [
    "offline",
    "slow_ms",
    "byzantine",
    "flapping",
    "flapping_mod",
    "drop_rpc_prob",
]


def _fault_payload() -> dict:
    data = state_payload()
    return {field: data[field] for field in FAULT_FIELDS}


class FaultsPayload(BaseModel):
    offline: bool | None = None
    slow_ms: int | None = Field(default=None, ge=0)
    byzantine: bool | None = None
    flapping: bool | None = None
    flapping_mod: int | None = Field(default=None, ge=0)
    drop_rpc_prob: float | None = Field(default=None, ge=0.0, le=1.0)


@router.get("/faults")
def get_faults() -> dict:
    return _fault_payload()


@router.put("/faults")
def update_faults(payload: FaultsPayload) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        update_state(**updates)
    return _fault_payload()
