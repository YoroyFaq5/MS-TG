import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.profile import get_profile, get_stats
from bot.presenters.profile import build_not_linked_message, build_profile_card
from bot.presenters.stats import build_stats_message
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["me"])
def handle_me(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = get_profile(api_client, telegram_id)
    except ApiError:
        logger.exception("/me failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить профиль, попробуйте позже.")
        return

    text, markup = build_profile_card(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["stats"])
def handle_stats(message) -> None:
    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = get_stats(api_client, telegram_id)
    except ApiError:
        logger.exception("/stats failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить статистику, попробуйте позже.")
        return

    text, markup = build_stats_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)
