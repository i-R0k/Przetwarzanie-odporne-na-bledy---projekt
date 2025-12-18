import asyncio
import random

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from vetclinic_api.admin.network_state import STATE, get_state


class ChaosMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if STATE.chaos_enabled:
            # Delay some requests to simulate network slowness.
            if random.random() < STATE.chaos_delay_rate:
                lo = min(STATE.chaos_delay_ms_min, STATE.chaos_delay_ms_max)
                hi = max(STATE.chaos_delay_ms_min, STATE.chaos_delay_ms_max)
                delay_ms = random.randint(lo, hi)
                await asyncio.sleep(delay_ms / 1000.0)

            # Inject 5xx errors on key blockchain endpoints; skip admin/metrics.
            path = request.url.path
            if path.startswith("/chain") or path.startswith("/tx") or path.startswith("/rpc"):
                if random.random() < STATE.chaos_error_rate:
                    return JSONResponse({"detail": "simulated_failure"}, status_code=500)

        return await call_next(request)


async def apply_rpc_faults(endpoint_name: str) -> None:
    state = get_state()

    if state.offline:
        raise HTTPException(status_code=503, detail="Node is offline (simulated)")

    if state.flapping and state.flapping_mod > 0:
        call_index = state.next_call_index(endpoint_name)
        if call_index % state.flapping_mod == 1:
            raise HTTPException(
                status_code=503, detail="RPC flapping (simulated)"
            )

    if state.slow_ms > 0:
        await asyncio.sleep(state.slow_ms / 1000.0)

    if state.should_drop():
        raise HTTPException(
            status_code=503, detail="Transient RPC drop (simulated)"
        )
