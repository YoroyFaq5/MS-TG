"""
Тестовые заглушки обязательных переменных окружения (см. bot/config.py) —
нужны, потому что часть тестов (webhooks/events) реально импортирует
bot.telegram_bot (создаёт TeleBot с этим токеном), а не только чистые
presenters. Заведомо фиктивные значения — сеть в тестах не дёргается,
send_message всегда мокается.
"""
import os
import sqlite3
import tempfile

import pytest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:TEST-FAKE-TOKEN")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("TELEGRAM_WEBHOOK_PATH_TOKEN", "test-path-token")
os.environ.setdefault("MAIN_API_BASE_URL", "http://localhost:9999")
os.environ.setdefault("MAIN_API_SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("INCOMING_EVENT_SECRET", "test-event-secret")

# bot/storage.py (FSM state, double-tap locks, notification prefs, outbox
# event dedup) needs its SQLite file/tables to exist before any test that
# exercises a handler/webhook touches it — tests never go through
# create_app() (which normally calls storage.init_db()), so it's done here
# once for the whole test session, against a throwaway temp file rather
# than the real bot/data/bot.db.
_tmp_db_dir = tempfile.mkdtemp(prefix="mafiabot_test_")
os.environ.setdefault("BOT_DB_PATH", os.path.join(_tmp_db_dir, "test_bot.db"))

from bot import storage  # noqa: E402

storage.init_db()


@pytest.fixture(autouse=True)
def _clear_action_locks():
    """Different tests reuse the same fake telegram user id + callback_data,
    and the whole suite runs in well under the 8s action-lock TTL — without
    this, a lock acquired by an earlier test's guarded_callback (sensitive=True)
    would still be held when a later, unrelated test exercises the same
    (actor, action) pair, making it wrongly see "already processing"."""
    with sqlite3.connect(storage.DB_PATH) as conn:
        conn.execute("DELETE FROM action_locks")
    yield
