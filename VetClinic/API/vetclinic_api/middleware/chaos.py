import asyncio
import random

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from vetclinic_api.admin.network_state import STATE


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
