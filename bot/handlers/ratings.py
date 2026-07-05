import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.ratings import get_ratings
from bot.presenters.ratings import build_ratings_message

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["rating"])
def handle_rating(message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    page = 1
    if len(parts) > 1 and parts[1].strip().isdigit():
        page = max(1, int(parts[1].strip()))

    try:
        data = get_ratings(api_client, scope="global", page=page, per_page=10)
    except ApiError:
        logger.exception("/rating failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить рейтинг, попробуйте позже.")
        return

    text, markup = build_ratings_message(data, scope="global")
    bot.send_message(message.chat.id, text, reply_markup=markup)
