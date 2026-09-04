import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.account import unlink
from bot.presenters.profile import build_not_linked_message
from bot.presenters.account import (
    build_unlink_confirm_message, build_unlink_done_message, build_unlink_cancelled_message,
)
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb
from bot.ui import error_state

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["unlink"])
def handle_unlink(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
    except ApiError:
        logger.exception("/unlink resolve failed")
        bot.send_message(message.chat.id, error_state("Не удалось проверить привязку."))
        return

    text, markup = build_unlink_confirm_message()
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "account", "unlink-confirm"))
@guarded_callback(bot)
def handle_unlink_confirm_screen(call) -> None:
    text, markup = build_unlink_confirm_message()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "account", "unlink-no"))
@guarded_callback(bot)
def handle_unlink_no(call) -> None:
    text, markup = build_unlink_cancelled_message()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "account", "unlink-yes"))
@guarded_callback(bot, sensitive=True)
def handle_unlink_yes(call) -> None:
    telegram_id = call.from_user.id
    try:
        unlink(api_client, telegram_id)
    except ApiError:
        logger.exception("/unlink confirm failed")
        bot.answer_callback_query(call.id, error_state("Не удалось отвязать."), show_alert=True)
        return

    text, _ = build_unlink_done_message()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Готово")
