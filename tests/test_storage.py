"""
bot/storage.py — the local SQLite-backed state the bot needs between
requests: FSM scenarios (gift-sending), double-tap/duplicate-submission
locks, outbox event dedup, and notification preferences. Uses the shared
test DB initialized once in conftest.py (BOT_DB_PATH), scoped per test via
random chat_id/keys so tests don't interfere with each other.
"""
import itertools

from bot import storage

_ids = itertools.count(900_000)


def _chat_id():
    return next(_ids)


def test_fsm_state_round_trip():
    chat_id = _chat_id()
    assert storage.get_fsm_state(chat_id) is None

    storage.set_fsm_state(chat_id, "gift_send", "await_recipient", {"inventory_item_id": 5})
    state = storage.get_fsm_state(chat_id)
    assert state == {"scenario": "gift_send", "step": "await_recipient", "data": {"inventory_item_id": 5}}


def test_fsm_state_overwrite():
    chat_id = _chat_id()
    storage.set_fsm_state(chat_id, "gift_send", "await_recipient", {})
    storage.set_fsm_state(chat_id, "gift_send", "await_note", {"to_player_id": 9})
    state = storage.get_fsm_state(chat_id)
    assert state["step"] == "await_note"
    assert state["data"] == {"to_player_id": 9}


def test_fsm_state_clear():
    chat_id = _chat_id()
    storage.set_fsm_state(chat_id, "gift_send", "await_recipient", {})
    storage.clear_fsm_state(chat_id)
    assert storage.get_fsm_state(chat_id) is None


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
