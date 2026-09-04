"""
Gift-sending FSM. State lives in bot/storage.py (SQLite), keyed by chat_id
— survives a process restart, unlike an in-memory dict (see storage.py
module docstring for why SQLite over Redis here).

Flow: pick item (callback, from gift hub or an inventory item's own
"🎁 Подарить" button) -> type recipient nickname (free text) -> pick from
search results (callback) -> optional note (free text or skip) -> confirm
(callback, shows item+recipient+note) -> send. "✖️ Отмена" is always one
tap away at every step.
"""
import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.gifts import get_inbox, get_history, get_giftable_items, send_gift
from bot.api_client.endpoints.players import search_players, get_player
from bot.presenters.gifts import (
    build_gifts_hub_message, build_inbox_message, build_history_message,
    build_pick_item_message, build_ask_recipient_message, build_recipient_results_message,
    build_ask_note_message, build_confirm_message, build_sent_message,
)
from bot.presenters.profile import build_not_linked_message
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import error_state
from bot import storage

logger = logging.getLogger(__name__)

SCENARIO = "gift_send"
MAX_NOTE_LENGTH = 200


def _edit(call, text, markup):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


def _state_step(chat_id: int, step: str) -> bool:
    state = storage.get_fsm_state(chat_id)
    return bool(state and state["scenario"] == SCENARIO and state["step"] == step)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "hub"))
@guarded_callback(bot)
def handle_gift_hub(call) -> None:
    storage.clear_fsm_state(call.message.chat.id)
    _edit(call, *build_gifts_hub_message())


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "inbox"))
@guarded_callback(bot)
def handle_gift_inbox(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    parts = parse_cb(call.data)
    page = int(parts[2]) if len(parts) > 2 else 1
    data = get_inbox(api_client, telegram_id, page=page)
    _edit(call, *build_inbox_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "history"))
@guarded_callback(bot)
def handle_gift_history(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    parts = parse_cb(call.data)
    page = int(parts[2]) if len(parts) > 2 else 1
    data = get_history(api_client, telegram_id, page=page)
    _edit(call, *build_history_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "send") and len(parse_cb(call.data)) == 2)
@guarded_callback(bot)
def handle_gift_send_start(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    storage.clear_fsm_state(call.message.chat.id)
    items = get_giftable_items(api_client, telegram_id)
    _edit(call, *build_pick_item_message(items))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "send-pick"))
@guarded_callback(bot)
def handle_gift_pick_item(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    _, _, inventory_item_id = parse_cb(call.data)
    storage.set_fsm_state(
        call.message.chat.id, SCENARIO, "await_recipient", {"inventory_item_id": int(inventory_item_id)},
    )
    _edit(call, *build_ask_recipient_message())


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "cancel"))
@guarded_callback(bot)
def handle_gift_cancel(call) -> None:
    storage.clear_fsm_state(call.message.chat.id)
    _edit(call, *build_gifts_hub_message())


@bot.message_handler(
    func=lambda m: _state_step(m.chat.id, "await_recipient"), content_types=["text"],
)
def handle_gift_recipient_text(message) -> None:
    query = (message.text or "").strip()
    if not query:
        return
    try:
        candidates = search_players(api_client, query)
    except ApiError:
        bot.send_message(message.chat.id, error_state("Поиск временно недоступен."))
        return
    my_player_id = resolve_player_id(api_client, message.from_user.id)
    candidates = [c for c in candidates if c["id"] != my_player_id][:8]
    text, markup = build_recipient_results_message(candidates, query)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "recip"))
@guarded_callback(bot)
def handle_gift_recipient_pick(call) -> None:
    state = storage.get_fsm_state(call.message.chat.id)
    if not state or state["scenario"] != SCENARIO:
        _edit(call, *build_gifts_hub_message())
        return
    _, _, to_player_id = parse_cb(call.data)
    to_player_id = int(to_player_id)
    data = state["data"]
    data["to_player_id"] = to_player_id
    storage.set_fsm_state(call.message.chat.id, SCENARIO, "await_note", data)

    recipient = get_player(api_client, to_player_id)
    text, markup = build_ask_note_message(recipient["display_name"])
    bot.send_message(call.message.chat.id, text, reply_markup=markup)
    bot.answer_callback_query(call.id)


def _show_confirm(chat_id: int) -> None:
    # Private chats only (this FSM never runs in a group) — chat_id and the
    # user's telegram_id are the same value there, so no separate lookup
    # is needed to call the API on the user's behalf.
    state = storage.get_fsm_state(chat_id)
    data = state["data"]

    giftable = get_giftable_items(api_client, chat_id)
    item_entry = next((i for i in giftable if i["id"] == data["inventory_item_id"]), None)
    item_name = item_entry["item"]["name"] if item_entry else "?"
    data["item_name"] = item_name
    storage.set_fsm_state(chat_id, SCENARIO, "confirm", data)

    recipient = get_player(api_client, data["to_player_id"])
    text, markup = build_confirm_message(item_name, recipient["display_name"], data.get("note") or "")
    bot.send_message(chat_id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "skip-note"))
@guarded_callback(bot)
def handle_gift_skip_note(call) -> None:
    if not _state_step(call.message.chat.id, "await_note"):
        _edit(call, *build_gifts_hub_message())
        return
    bot.answer_callback_query(call.id)
    _show_confirm(call.message.chat.id)


@bot.message_handler(func=lambda m: _state_step(m.chat.id, "await_note"), content_types=["text"])
def handle_gift_note_text(message) -> None:
    note = (message.text or "").strip()[:MAX_NOTE_LENGTH]
    state = storage.get_fsm_state(message.chat.id)
    data = state["data"]
    data["note"] = note
    storage.set_fsm_state(message.chat.id, SCENARIO, "await_note", data)
    _show_confirm(message.chat.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gift", "confirm"))
@guarded_callback(bot, sensitive=True)
def handle_gift_confirm(call) -> None:
    state = storage.get_fsm_state(call.message.chat.id)
    if not state or state["scenario"] != SCENARIO:
        _edit(call, *build_gifts_hub_message())
        return
    data = state["data"]
    telegram_id = call.from_user.id

    try:
        send_gift(
            api_client, telegram_id, data["inventory_item_id"], data["to_player_id"],
            data.get("note") or None,
        )
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return

    recipient = get_player(api_client, data["to_player_id"])
    storage.clear_fsm_state(call.message.chat.id)
    text, markup = build_sent_message(data.get("item_name", "подарок"), recipient["display_name"])
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Отправлено 🎁")
