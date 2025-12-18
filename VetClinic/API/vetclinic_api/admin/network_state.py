from pydantic import BaseModel, Field


class NetworkSimState(BaseModel):
    traffic_enabled: bool = True
    traffic_rps: float = Field(default=1.0, ge=0.0, le=50.0)  # approximate requests/sec
    chaos_enabled: bool = False
    chaos_error_rate: float = Field(default=0.02, ge=0.0, le=1.0)  # % 5xx
    chaos_delay_rate: float = Field(default=0.05, ge=0.0, le=1.0)  # % delays
    chaos_delay_ms_min: int = Field(default=50, ge=0, le=5000)
    chaos_delay_ms_max: int = Field(default=300, ge=0, le=5000)


STATE = NetworkSimState()
