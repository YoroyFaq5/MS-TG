import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.inventory import get_inventory, equip, unequip
from bot.presenters.inventory import build_inventory_hub_message, build_inventory_list_message
from bot.presenters.profile import build_not_linked_message
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb

logger = logging.getLogger(__name__)


def _cat(raw: str):
    return None if raw == "-" else raw


def _edit(call, text, markup):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "inv", "hub"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_inventory_hub(call) -> None:
    _edit(call, *build_inventory_hub_message())


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "inv", "list"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_inventory_list(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        _edit(call, *build_not_linked_message())
        return
    parts = parse_cb(call.data)
    category = _cat(parts[2]) if len(parts) > 2 else None
    items = get_inventory(api_client, telegram_id, category=category)
    _edit(call, *build_inventory_list_message(items, category))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "inv", "equip"))
@guarded_callback(bot, sensitive=True, private_only=True)
def handle_inventory_equip(call) -> None:
    _, _, inventory_item_id, category_raw = parse_cb(call.data)
    category = _cat(category_raw)
    telegram_id = call.from_user.id
    try:
        equip(api_client, telegram_id, int(inventory_item_id))
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    items = get_inventory(api_client, telegram_id, category=category)
    text, markup = build_inventory_list_message(items, category)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Экипировано ✅")


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "inv", "unequip"))
@guarded_callback(bot, sensitive=True, private_only=True)
def handle_inventory_unequip(call) -> None:
    _, _, inventory_item_id, category_raw = parse_cb(call.data)
    category = _cat(category_raw)
    telegram_id = call.from_user.id
    try:
        unequip(api_client, telegram_id, int(inventory_item_id))
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    items = get_inventory(api_client, telegram_id, category=category)
    text, markup = build_inventory_list_message(items, category)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Снято")
