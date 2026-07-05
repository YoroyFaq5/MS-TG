import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.profile import compare
from bot.presenters.profile import build_not_linked_message
from bot.presenters.compare import build_compare_message
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


@bot.message_handler(commands=["compare"])
def handle_compare(message) -> None:
    telegram_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        bot.send_message(
            message.chat.id,
            "Использование: <code>/compare &lt;id игрока&gt;</code>",
        )
        return
    opponent_id = int(parts[1].strip())

    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = compare(api_client, telegram_id, opponent_id)
    except ApiNotFound:
        bot.send_message(message.chat.id, "Игрок с таким id не найден.")
        return
    except ApiError:
        logger.exception("/compare failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось сравнить, попробуйте позже.")
        return

    text, markup = build_compare_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)
