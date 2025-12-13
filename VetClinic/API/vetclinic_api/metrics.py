from __future__ import annotations

import os
import time
from typing import Callable, Optional

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Stała nazwa noda (node1..node6) z env, żeby nie robić losowej kardynalności
NODE_NAME = os.getenv("NODE_NAME", "node-local")

metrics_router = APIRouter(tags=["metrics"])

# -----------------------
# HTTP metrics
# -----------------------
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

http_exceptions_total = Counter(
    "http_exceptions_total",
    "Total number of exceptions raised during request handling",
    ["exception_type", "path"],
)

# -----------------------
# Blockchain / consensus metrics (minimum Stage 1)
# -----------------------
blockchain_chain_height = Gauge(
    "blockchain_chain_height",
    "Current blockchain height on node",
    ["node"],
)

blockchain_mempool_size = Gauge(
    "blockchain_mempool_size",
    "Current mempool size on node",
    ["node"],
)

tx_submitted_total = Counter(
    "tx_submitted_total",
    "Total transactions submitted/accepted by node",
    ["node"],
)

tx_rejected_total = Counter(
    "tx_rejected_total",
    "Total transactions rejected by node",
    ["node", "reason"],
)

consensus_votes_total = Counter(
    "consensus_votes_total",
    "Total votes cast by node",
    ["node", "vote"],  # yes|no|timeout|error
)

chain_verify_total = Counter(
    "chain_verify_total",
    "Total chain verification runs",
    ["node", "result"],  # ok|invalid|error
)

chain_verify_duration_seconds = Histogram(
    "chain_verify_duration_seconds",
    "Chain verification duration in seconds",
    ["node"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

# -----------------------
# Helpers
# -----------------------
def _normalized_path(request: Request) -> str:
    """
    Zwraca path w wersji "route template", np. /animals/{animal_id} zamiast /animals/123.
    To minimalizuje kardynalność metryk.
    """
    try:
        route = request.scope.get("route")
        if route and getattr(route, "path", None):
            return route.path
    except Exception:
        pass
    return request.url.path


async def instrumentator_middleware(request: Request, call_next: Callable):
    path = _normalized_path(request)
    method = request.method

    start = time.perf_counter()
    try:
        response = await call_next(request)
        status = str(getattr(response, "status_code", 500))
        return response
    except Exception as e:
        http_exceptions_total.labels(type(e).__name__, path).inc()
        # FastAPI i tak zamieni to na 500, ale metryka ma widzieć wyjątek
        raise
    finally:
        elapsed = time.perf_counter() - start
        # status może nie istnieć jeśli wyjątek poleciał zanim response powstał
        status_val = locals().get("status", "500")
        http_requests_total.labels(method, path, status_val).inc()
        http_request_duration_seconds.labels(method, path).observe(elapsed)


def set_chain_status(height: int, mempool_size: int, node: Optional[str] = None) -> None:
    n = node or NODE_NAME
    blockchain_chain_height.labels(n).set(height)
    blockchain_mempool_size.labels(n).set(mempool_size)


def inc_tx_submitted(node: Optional[str] = None) -> None:
    (tx_submitted_total.labels(node or NODE_NAME)).inc()


def inc_tx_rejected(reason: str, node: Optional[str] = None) -> None:
    (tx_rejected_total.labels(node or NODE_NAME, reason)).inc()


def inc_vote(vote: str, node: Optional[str] = None) -> None:
    (consensus_votes_total.labels(node or NODE_NAME, vote)).inc()


@metrics_router.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
