import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.profile import resolve
from bot.presenters.profile import build_not_linked_message, build_welcome_back_message

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["start"])
def handle_start(message) -> None:
    telegram_id = message.from_user.id
    try:
        data = resolve(api_client, telegram_id)
    except ApiError:
        logger.exception("resolve() failed for /start")
        bot.send_message(message.chat.id, "⚠️ Не удалось связаться с сайтом, попробуйте позже.")
        return

    if data.get("linked"):
        text, markup = build_welcome_back_message(data["display_name"])
    else:
        text, markup = build_not_linked_message()
    bot.send_message(message.chat.id, text, reply_markup=markup)
