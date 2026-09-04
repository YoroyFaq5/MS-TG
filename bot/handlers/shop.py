import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.shop import get_items, get_item_detail, buy_item
from bot.presenters.shop import (
    build_shop_hub_message, build_shop_list_message, build_shop_item_message,
    build_buy_confirm_message, build_buy_result_message,
)
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import stale_state

logger = logging.getLogger(__name__)


def _cat(raw: str):
    return None if raw == "-" else raw


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "shop", "hub"))
@guarded_callback(bot)
def handle_shop_hub(call) -> None:
    text, markup = build_shop_hub_message()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "shop", "list"))
@guarded_callback(bot)
def handle_shop_list(call) -> None:
    _, _, category_raw, page = parse_cb(call.data)
    category = _cat(category_raw)
    telegram_id = call.from_user.id
    data = get_items(api_client, category=category, telegram_id=telegram_id, page=int(page))
    text, markup = build_shop_list_message(data, category)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "shop", "item"))
@guarded_callback(bot)
def handle_shop_item(call) -> None:
    _, _, item_id, category_raw = parse_cb(call.data)
    category = _cat(category_raw)
    telegram_id = call.from_user.id
    try:
        item = get_item_detail(api_client, int(item_id), telegram_id=telegram_id)
    except ApiNotFound:
        bot.edit_message_text(
            stale_state("Товар больше не найден."), call.message.chat.id, call.message.message_id,
        )
        bot.answer_callback_query(call.id)
        return
    text, markup = build_shop_item_message(item, category)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "shop", "buy-confirm"))
@guarded_callback(bot)
def handle_shop_buy_confirm(call) -> None:
    _, _, item_id, category_raw = parse_cb(call.data)
    category = _cat(category_raw)
    telegram_id = call.from_user.id
    item = get_item_detail(api_client, int(item_id), telegram_id=telegram_id)
    text, markup = build_buy_confirm_message(item, category)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "shop", "buy"))
@guarded_callback(bot, sensitive=True)
def handle_shop_buy(call) -> None:
    _, _, item_id, category_raw = parse_cb(call.data)
    category = _cat(category_raw)
    telegram_id = call.from_user.id
    try:
        buy_item(api_client, telegram_id, int(item_id))
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    item = get_item_detail(api_client, int(item_id), telegram_id=telegram_id)
    text, markup = build_buy_result_message(
        f"«{item['name']}» куплен за {item['price']:.0f} монет.", item, category,
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Готово ✅")
