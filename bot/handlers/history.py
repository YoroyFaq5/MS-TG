import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.history import get_history
from bot.presenters.profile import build_not_linked_message
from bot.presenters.history import build_history_message
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["history"])
def handle_history(message) -> None:
    telegram_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)
    page = 1
    if len(parts) > 1 and parts[1].strip().isdigit():
        page = max(1, int(parts[1].strip()))

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = get_history(api_client, telegram_id, page=page, per_page=10)
    except ApiError:
        logger.exception("/history failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить историю, попробуйте позже.")
        return

    text, markup = build_history_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)
