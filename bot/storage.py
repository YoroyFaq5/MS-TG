"""
Local persistent storage for the bot — the "по факту необходимости" local
DB ARCHITECTURE.md always said would show up once something bot-specific
needed state between requests that doesn't fit in callback_data. Three
things now need exactly that:

1. Multi-step scenarios (FSM) — e.g. "send a gift": pick item -> pick
   recipient -> optional note -> confirm. The in-progress selection has to
   survive between one Telegram update and the next.
2. Idempotency — de-duplicating a double-tapped button (a purchase/gift/
   fantasy-draft action) and de-duplicating a retried outbox event
   (event_id) from the main site so a retry never sends a second message.
3. Per-user notification category preferences (chat-noise control, purely
   a bot-UX setting — not a business rule the site needs to know about).

Choice: **SQLite via the stdlib `sqlite3` module**, one file
(`bot/data/bot.db` by default, override with `BOT_DB_PATH`) — not Redis.
Reasoning: this bot runs as a single small Flask/WSGI app (PythonAnywhere,
webhook model, no dedicated worker/infra already running), so Redis would
be a new service to provision and operate for a handful of small tables
with light write volume. SQLite needs zero extra infrastructure, the
stdlib driver has no new dependency, and a file survives process restarts
(unlike an in-memory dict). If this bot ever needs to scale to multiple
concurrent app instances sharing state (it currently doesn't — PythonAnywhere
serves it from one worker), that's the trigger to revisit and move to
Redis/Postgres; noted in ARCHITECTURE.md as the explicit next step.

All functions here are small, synchronous, and open/close their own
connection per call — call volume is low (one row read/write per handled
update at most), so pooling would be premature.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Iterator, Optional

_DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")
DB_PATH = os.environ.get("BOT_DB_PATH", _DEFAULT_DB_PATH)

_ACTION_LOCK_TTL_SECONDS = 8.0
_PROCESSED_EVENT_RETENTION_SECONDS = 7 * 24 * 3600  # 7 days is plenty for outbox retries


def _ensure_dir() -> None:
    directory = os.path.dirname(DB_PATH)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH, timeout=5.0, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
    finally:
        conn.close()


def _migrate_fsm_state_schema(conn: sqlite3.Connection) -> None:
    """fsm_state used to be keyed by chat_id alone — unusable once a group
    chat can have several users each mid-scenario at once (they'd stomp on
    each other's state). Composite-key it on (chat_id, telegram_user_id)
    instead (CLAUDE_TASK_BOT_RU_GROUPS.md, п.2.3).

    Lossless backfill: every row that existed under the old schema was
    necessarily created in a PRIVATE chat (FSM never ran anywhere else
    before this migration) — and Telegram's own convention makes a private
    chat's chat_id equal to the user's telegram_id. So telegram_user_id =
    chat_id is exact, not a guess, for every pre-existing row."""
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='fsm_state'"
    ).fetchone()
    if not table_exists:
        return  # fresh install — the CREATE TABLE below already uses the new schema
    cols = [row[1] for row in conn.execute("PRAGMA table_info(fsm_state)").fetchall()]
    if "telegram_user_id" in cols:
        return  # already migrated

    conn.execute("ALTER TABLE fsm_state RENAME TO fsm_state_old")
    conn.execute(
        """CREATE TABLE fsm_state (
            chat_id INTEGER NOT NULL,
            telegram_user_id INTEGER NOT NULL,
            scenario TEXT NOT NULL,
            step TEXT NOT NULL,
            data TEXT NOT NULL DEFAULT '{}',
            updated_at REAL NOT NULL,
            PRIMARY KEY (chat_id, telegram_user_id)
        )"""
    )
    conn.execute(
        """INSERT INTO fsm_state (chat_id, telegram_user_id, scenario, step, data, updated_at)
           SELECT chat_id, chat_id, scenario, step, data, updated_at FROM fsm_state_old"""
    )
    conn.execute("DROP TABLE fsm_state_old")


def init_db() -> None:
    """Create tables if missing — idempotent, safe to call on every boot
    (same spirit as the main site's ensure_year_exists), and explicitly
    called once from tests/conftest.py against a temp file per test run."""
    with _conn() as conn:
        _migrate_fsm_state_schema(conn)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS fsm_state (
                chat_id INTEGER NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                scenario TEXT NOT NULL,
                step TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                updated_at REAL NOT NULL,
                PRIMARY KEY (chat_id, telegram_user_id)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS action_locks (
                lock_key TEXT PRIMARY KEY,
                expires_at REAL NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS processed_events (
                event_id TEXT PRIMARY KEY,
                received_at REAL NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS notification_prefs (
                telegram_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                PRIMARY KEY (telegram_id, category)
            )"""
        )


# ── FSM state (multi-step scenarios: gift-sending, etc.) ────────────────────

def get_fsm_state(chat_id: int, telegram_user_id: int) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT scenario, step, data FROM fsm_state WHERE chat_id = ? AND telegram_user_id = ?",
            (chat_id, telegram_user_id),
        ).fetchone()
    if not row:
        return None
    scenario, step, data = row
    try:
        payload = json.loads(data)
    except ValueError:
        payload = {}
    return {"scenario": scenario, "step": step, "data": payload}


def set_fsm_state(
    chat_id: int, telegram_user_id: int, scenario: str, step: str, data: Optional[dict] = None,
) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT INTO fsm_state (chat_id, telegram_user_id, scenario, step, data, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(chat_id, telegram_user_id) DO UPDATE SET
                   scenario=excluded.scenario, step=excluded.step,
                   data=excluded.data, updated_at=excluded.updated_at""",
            (chat_id, telegram_user_id, scenario, step, json.dumps(data or {}), time.time()),
        )


def clear_fsm_state(chat_id: int, telegram_user_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "DELETE FROM fsm_state WHERE chat_id = ? AND telegram_user_id = ?", (chat_id, telegram_user_id),
        )


# ── Double-tap / duplicate-submission guard ──────────────────────────────────

def try_acquire_action_lock(lock_key: str, ttl_seconds: float = _ACTION_LOCK_TTL_SECONDS) -> bool:
    """
    Best-effort guard against a sensitive action (purchase, gift, fantasy
    draft creation, achievement pin toggle, ...) being triggered twice by a
    fast double-tap. Returns True if the caller won the lock and should
    proceed, False if another in-flight (or very recent) call already holds
    it. `lock_key` should identify the exact action + actor, e.g.
    f"buy:{telegram_id}:{item_id}". The lock expires on its own after
    `ttl_seconds` — callers do not need to release it explicitly (a normal
    request completes in well under the TTL; if a process crashes mid-
    request the lock simply expires rather than jamming the action forever).
    """
    now = time.time()
    with _conn() as conn:
        conn.execute("DELETE FROM action_locks WHERE expires_at < ?", (now,))
        try:
            conn.execute(
                "INSERT INTO action_locks (lock_key, expires_at) VALUES (?, ?)",
                (lock_key, now + ttl_seconds),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def release_action_lock(lock_key: str) -> None:
    """Optional early release once an action genuinely completes, so a
    legitimate follow-up (e.g. re-opening the same item after a successful
    purchase) isn't stuck waiting out the full TTL."""
    with _conn() as conn:
        conn.execute("DELETE FROM action_locks WHERE lock_key = ?", (lock_key,))


# ── Outbox event idempotency (site -> bot notifications) ────────────────────

def is_event_processed(event_id: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,)
        ).fetchone()
    return row is not None


def mark_event_processed(event_id: str) -> None:
    now = time.time()
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_events (event_id, received_at) VALUES (?, ?)",
            (event_id, now),
        )
        # Light housekeeping on every write rather than a separate cron —
        # volume is low enough that this is cheap, and it keeps the table
        # from growing unbounded without needing a scheduled job.
        conn.execute(
            "DELETE FROM processed_events WHERE received_at < ?",
            (now - _PROCESSED_EVENT_RETENTION_SECONDS,),
        )


# ── Notification preferences ─────────────────────────────────────────────────

# Category keys are deliberately short and stable — they're used verbatim in
# callback_data for the settings screen.
NOTIFICATION_CATEGORIES: dict[str, str] = {
    "slot": "🎲 Моя следующая рассадка",
    "tourn": "🏆 Начало/изменение турнира или вечера серии",
    "game": "🎮 Завершение моей игры",
    "rating": "📈 Изменение рейтинга/места сезона",
    "award": "🎖 Достижение или титул",
    "fantasy": "🎯 Фэнтези: блокировка, результат, приз",
    "gift": "🎁 Подарок",
    "shop": "🛍 Покупка/перекуп предмета",
    "season": "🏁 Сезонная награда и «Стол года»",
}


def get_notification_prefs(telegram_id: int) -> dict[str, bool]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT category, enabled FROM notification_prefs WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchall()
    stored = {category: bool(enabled) for category, enabled in rows}
    # Default: everything ON until the user explicitly opts out — matches
    # today's behaviour (no preferences existed, everything was sent).
    return {key: stored.get(key, True) for key in NOTIFICATION_CATEGORIES}


def set_notification_pref(telegram_id: int, category: str, enabled: bool) -> None:
    if category not in NOTIFICATION_CATEGORIES:
        return
    with _conn() as conn:
        conn.execute(
            """INSERT INTO notification_prefs (telegram_id, category, enabled)
               VALUES (?, ?, ?)
               ON CONFLICT(telegram_id, category) DO UPDATE SET enabled=excluded.enabled""",
            (telegram_id, category, int(enabled)),
        )


def is_notification_enabled(telegram_id: int, category: str) -> bool:
    if category not in NOTIFICATION_CATEGORIES:
        return True
    with _conn() as conn:
        row = conn.execute(
            "SELECT enabled FROM notification_prefs WHERE telegram_id = ? AND category = ?",
            (telegram_id, category),
        ).fetchone()
    return bool(row[0]) if row else True
