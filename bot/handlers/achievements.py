import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.achievements import get_achievements, pin, unpin, get_titles
from bot.presenters.profile import build_not_linked_message
from bot.presenters.achievements import build_achievements_message, build_titles_message
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["achievements"])
def handle_achievements(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        items = get_achievements(api_client, telegram_id)
    except ApiError:
        logger.exception("/achievements failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить достижения, попробуйте позже.")
        return

    text, markup = build_achievements_message(items)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("ach:"))
def handle_achievement_toggle_callback(call) -> None:
    _, action, achievement_id = call.data.split(":", 2)
    achievement_id = int(achievement_id)
    telegram_id = call.from_user.id
    action_fn = pin if action == "pin" else unpin

    try:
        action_fn(api_client, telegram_id, achievement_id)
        items = get_achievements(api_client, telegram_id)
    except ApiError:
        logger.exception("achievement pin/unpin toggle failed")
        bot.answer_callback_query(call.id, "⚠️ Не удалось выполнить действие, попробуйте позже.")
        return

    text, markup = build_achievements_message(items)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Готово ✅")


@bot.message_handler(commands=["titles"])
def handle_titles(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        items = get_titles(api_client, telegram_id)
    except ApiError:
        logger.exception("/titles failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить титулы, попробуйте позже.")
        return

    text, markup = build_titles_message(items)
    bot.send_message(message.chat.id, text, reply_markup=markup)
