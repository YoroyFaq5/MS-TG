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


# ── Group-command antispam (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 7) ─────────
# Two windows per (chat_id, user_id) — a tight short-burst cap and a looser
# longer one — configured via bot/config.py so an operator can tune them
# without a code change. Separate from check_rate_limit() above (that one
# guards the two webhook routes themselves, keyed differently).

_last_group_warning: dict[str, float] = {}


def check_group_command_rate_limit(chat_id: int, user_id: int) -> tuple[bool, bool]:
    """Returns (allowed, should_warn). should_warn is True at most once per
    short window even if the caller keeps sending commands past the limit —
    "отвечать тихим коротким сообщением не чаще одного раза за окно"."""
    from bot.config import Config

    key = f"group:{chat_id}:{user_id}"
    short_ok = check_rate_limit(
        f"{key}:s", Config.GROUP_COMMAND_LIMIT_SHORT, Config.GROUP_COMMAND_WINDOW_SHORT_SECONDS,
    )
    long_ok = check_rate_limit(
        f"{key}:l", Config.GROUP_COMMAND_LIMIT_LONG, Config.GROUP_COMMAND_WINDOW_LONG_SECONDS,
    )
    if short_ok and long_ok:
        return True, False

    now = time.monotonic()
    last = _last_group_warning.get(key, 0.0)
    should_warn = (now - last) >= Config.GROUP_COMMAND_WINDOW_SHORT_SECONDS
    if should_warn:
        _last_group_warning[key] = now
    return False, should_warn
