from fastapi import APIRouter

from .network_state import STATE, NetworkSimState

router = APIRouter(prefix="/admin/network", tags=["admin-network"])


@router.get("/sim", response_model=NetworkSimState)
def get_sim_state():
    return STATE


@router.put("/sim", response_model=NetworkSimState)
def set_sim_state(new_state: NetworkSimState):
    # podmieniamy wartości "w miejscu"
    STATE.traffic_enabled = new_state.traffic_enabled
    STATE.traffic_rps = new_state.traffic_rps
    STATE.chaos_enabled = new_state.chaos_enabled
    STATE.chaos_error_rate = new_state.chaos_error_rate
    STATE.chaos_delay_rate = new_state.chaos_delay_rate
    STATE.chaos_delay_ms_min = new_state.chaos_delay_ms_min
    STATE.chaos_delay_ms_max = new_state.chaos_delay_ms_max
    return STATE
