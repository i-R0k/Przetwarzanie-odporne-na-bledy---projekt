from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from vetclinic_api.cluster.faults import FaultConfig, FAULTS

router = APIRouter(prefix="/admin", tags=["admin"])


class FaultsPayload(BaseModel):
    offline: bool | None = None
    slow_ms: int | None = Field(default=None, ge=0)
    byzantine: bool | None = None
    flapping: bool | None = None
    flapping_mod: int | None = Field(default=None, ge=0)
    drop_rpc_prob: float | None = Field(default=None, ge=0.0, le=1.0)


@router.get("/faults")
def get_faults() -> dict:
    return asdict(FAULTS)


@router.put("/faults")
def update_faults(payload: FaultsPayload) -> dict:
    global FAULTS
    current = asdict(FAULTS)
    updates = payload.model_dump(exclude_unset=True)
    current.update({k: v for k, v in updates.items() if v is not None})
    FAULTS = FaultConfig(**current)
    return asdict(FAULTS)
