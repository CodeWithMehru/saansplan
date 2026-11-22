"""Structured logging helpers that never receive free text or secrets."""

import json
import logging
import time


def log_request(request_id: str, route: str, status: int, started: float) -> None:
    """Emit a compact JSON access record without coordinates or body text."""
    logging.getLogger("saansplan.access").info(
        json.dumps(
            {
                "request_id": request_id,
                "route": route,
                "status": status,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
    )
