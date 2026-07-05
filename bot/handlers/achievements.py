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


def _pin_or_unpin(message, action) -> None:
    telegram_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        bot.send_message(message.chat.id, "Использование: <code>/pin &lt;id достижения&gt;</code>")
        return
    achievement_id = int(parts[1].strip())

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        action(api_client, telegram_id, achievement_id)
    except ApiError:
        logger.exception("pin/unpin failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось выполнить действие, попробуйте позже.")
        return

    bot.send_message(message.chat.id, "Готово ✅")


@bot.message_handler(commands=["pin"])
def handle_pin(message) -> None:
    _pin_or_unpin(message, pin)


@bot.message_handler(commands=["unpin"])
def handle_unpin(message) -> None:
    _pin_or_unpin(message, unpin)


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
