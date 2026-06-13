"""Prometheus instrumentation for Urban Data Explorer API.

Exposes:
- ude_http_requests_total{method, path, status}   : counter
- ude_http_request_duration_seconds{method, path} : histogram (p50/p95/p99)

Mount via the FastAPI middleware stack in main.py.
The /metrics endpoint is registered separately as a plain route.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

REQUEST_COUNT = Counter(
    "ude_http_requests_total",
    "Total HTTP request count",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "ude_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


async def prometheus_middleware(request: Request, call_next: Callable) -> Response:
    """Record per-route request count and latency."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    # Use the route template (e.g. /datamarts/dashboard) rather than the raw
    # URL to avoid cardinality explosion from path parameters.
    route = request.scope.get("route")
    path = route.path if route else request.url.path

    REQUEST_COUNT.labels(
        method=request.method,
        path=path,
        status=str(response.status_code),
    ).inc()
    REQUEST_LATENCY.labels(method=request.method, path=path).observe(duration)

    return response


def metrics_endpoint() -> Response:
    """Return Prometheus text format metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
