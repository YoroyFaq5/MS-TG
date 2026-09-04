"""
bot/storage.py — the local SQLite-backed state the bot needs between
requests: FSM scenarios (gift-sending), double-tap/duplicate-submission
locks, outbox event dedup, and notification preferences. Uses the shared
test DB initialized once in conftest.py (BOT_DB_PATH), scoped per test via
random chat_id/keys so tests don't interfere with each other.
"""
import itertools
import sqlite3

from bot import storage

_ids = itertools.count(900_000)


def test_fsm_state_schema_migration_backfills_user_id_from_chat_id():
    """A pre-migration DB has fsm_state keyed by chat_id alone. Since FSM
    only ever ran in private chats before this migration, chat_id IS the
    user's telegram_id there (Telegram's own convention) — the migration
    must backfill telegram_user_id = chat_id losslessly, not drop the row."""
    old_chat_id = 777_777

    with sqlite3.connect(storage.DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS fsm_state")
        conn.execute(
            """CREATE TABLE fsm_state (
                chat_id INTEGER PRIMARY KEY,
                scenario TEXT NOT NULL,
                step TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                updated_at REAL NOT NULL
            )"""
        )
        conn.execute(
            "INSERT INTO fsm_state (chat_id, scenario, step, data, updated_at) VALUES (?, ?, ?, ?, ?)",
            (old_chat_id, "gift_send", "await_note", '{"to_player_id": 3}', 0.0),
        )

    storage.init_db()  # must run the migration idempotently

    state = storage.get_fsm_state(old_chat_id, old_chat_id)
    assert state == {"scenario": "gift_send", "step": "await_note", "data": {"to_player_id": 3}}

    # Idempotent — calling init_db() again must not error or duplicate/lose the row.
    storage.init_db()
    assert storage.get_fsm_state(old_chat_id, old_chat_id) is not None


def _chat_id():
    return next(_ids)


def test_fsm_state_round_trip():
    chat_id = _chat_id()
    assert storage.get_fsm_state(chat_id, chat_id) is None

    storage.set_fsm_state(chat_id, chat_id, "gift_send", "await_recipient", {"inventory_item_id": 5})
    state = storage.get_fsm_state(chat_id, chat_id)
    assert state == {"scenario": "gift_send", "step": "await_recipient", "data": {"inventory_item_id": 5}}


def test_fsm_state_overwrite():
    chat_id = _chat_id()
    storage.set_fsm_state(chat_id, chat_id, "gift_send", "await_recipient", {})
    storage.set_fsm_state(chat_id, chat_id, "gift_send", "await_note", {"to_player_id": 9})
    state = storage.get_fsm_state(chat_id, chat_id)
    assert state["step"] == "await_note"
    assert state["data"] == {"to_player_id": 9}


def test_fsm_state_clear():
    chat_id = _chat_id()
    storage.set_fsm_state(chat_id, chat_id, "gift_send", "await_recipient", {})
    storage.clear_fsm_state(chat_id, chat_id)
    assert storage.get_fsm_state(chat_id, chat_id) is None


def test_fsm_state_isolated_per_user_in_same_chat():
    """CLAUDE_TASK_BOT_RU_GROUPS.md п.2.3: two different users' scenarios
    in the SAME chat (a group, in principle) must not collide — the old
    chat_id-only key would have let one user's state clobber another's."""
    chat_id = _chat_id()
    user_a, user_b = 111111, 222222

    storage.set_fsm_state(chat_id, user_a, "gift_send", "await_recipient", {"inventory_item_id": 1})
    storage.set_fsm_state(chat_id, user_b, "gift_send", "await_note", {"to_player_id": 9})

    state_a = storage.get_fsm_state(chat_id, user_a)
    state_b = storage.get_fsm_state(chat_id, user_b)
    assert state_a["step"] == "await_recipient" and state_a["data"] == {"inventory_item_id": 1}
    assert state_b["step"] == "await_note" and state_b["data"] == {"to_player_id": 9}

    storage.clear_fsm_state(chat_id, user_a)
    assert storage.get_fsm_state(chat_id, user_a) is None
    assert storage.get_fsm_state(chat_id, user_b) is not None  # untouched


def test_action_lock_blocks_second_acquisition_within_ttl():
    key = f"buy:{_chat_id()}:1"
    assert storage.try_acquire_action_lock(key, ttl_seconds=5) is True
    assert storage.try_acquire_action_lock(key, ttl_seconds=5) is False


def test_action_lock_different_keys_are_independent():
    key_a = f"buy:{_chat_id()}:1"
    key_b = f"buy:{_chat_id()}:2"
    assert storage.try_acquire_action_lock(key_a) is True
    assert storage.try_acquire_action_lock(key_b) is True


def test_action_lock_release_allows_immediate_reacquire():
    key = f"buy:{_chat_id()}:1"
    storage.try_acquire_action_lock(key, ttl_seconds=30)
    storage.release_action_lock(key)
    assert storage.try_acquire_action_lock(key, ttl_seconds=30) is True


def test_action_lock_expires_after_ttl():
    import time as _time

    key = f"buy:{_chat_id()}:1"
    assert storage.try_acquire_action_lock(key, ttl_seconds=0.1) is True
    _time.sleep(0.15)
    assert storage.try_acquire_action_lock(key, ttl_seconds=0.1) is True


def test_event_dedup_marks_and_checks():
    event_id = f"evt-{_chat_id()}"
    assert storage.is_event_processed(event_id) is False
    storage.mark_event_processed(event_id)
    assert storage.is_event_processed(event_id) is True


def test_event_dedup_mark_twice_is_idempotent():
    event_id = f"evt-{_chat_id()}"
    storage.mark_event_processed(event_id)
    storage.mark_event_processed(event_id)  # must not raise (INSERT OR IGNORE)
    assert storage.is_event_processed(event_id) is True


def test_notification_prefs_default_to_enabled():
    telegram_id = _chat_id()
    prefs = storage.get_notification_prefs(telegram_id)
    assert set(prefs.keys()) == set(storage.NOTIFICATION_CATEGORIES.keys())
    assert all(prefs.values())
    assert storage.is_notification_enabled(telegram_id, "gift") is True


def test_notification_prefs_can_be_disabled_and_re_enabled():
    telegram_id = _chat_id()
    storage.set_notification_pref(telegram_id, "gift", False)
    assert storage.is_notification_enabled(telegram_id, "gift") is False
    # Unrelated categories stay unaffected.
    assert storage.is_notification_enabled(telegram_id, "shop") is True

    storage.set_notification_pref(telegram_id, "gift", True)
    assert storage.is_notification_enabled(telegram_id, "gift") is True


def test_notification_prefs_unknown_category_is_ignored():
    telegram_id = _chat_id()
    storage.set_notification_pref(telegram_id, "not_a_real_category", False)
    assert storage.is_notification_enabled(telegram_id, "not_a_real_category") is True
