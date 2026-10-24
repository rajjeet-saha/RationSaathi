"""Minimal in-process rate limiter.

Suitable for the single-process prototype; a production deployment should use a
shared store (for example Redis) so limits are enforced across workers.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request, *, key: str, limit: int = 30, window_seconds: int = 60) -> None:
    client = request.client.host if request.client else "unknown"
    bucket_key = f"{key}:{client}"
    now = time.monotonic()
    bucket = _BUCKETS[bucket_key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests. Try again shortly.")
    bucket.append(now)


def reset_rate_limits() -> None:
    _BUCKETS.clear()
