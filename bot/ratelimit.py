"""
Minimal in-process rate limiter for the two public webhook endpoints
(Telegram updates, incoming site events). Same trade-off as MS's own
`app/routes/api_bot.py` limiter: per-process counters, not distributed —
good enough to blunt an obvious flood without adding Redis/nginx config
for a single small WSGI app. A real deployment behind nginx should also
set `limit_req` there; this is the in-app backstop.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

_WINDOW_SECONDS = 60
_DEFAULT_LIMIT = 600  # generous — Telegram itself is the main legitimate caller
_buckets: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str, limit: int = _DEFAULT_LIMIT, window_seconds: float = _WINDOW_SECONDS) -> bool:
    now = time.monotonic()
    bucket = _buckets[key]
    cutoff = now - window_seconds
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True
