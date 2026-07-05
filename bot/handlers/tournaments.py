import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.tournaments import get_tournaments, get_tournament_detail
from bot.presenters.tournaments import build_tournaments_list_message, build_tournament_detail_message

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"pending", "active", "finished"}


@bot.message_handler(commands=["tournaments"])
def handle_tournaments(message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    status = parts[1].strip() if len(parts) > 1 and parts[1].strip() in _VALID_STATUSES else None

    try:
        data = get_tournaments(api_client, status=status)
    except ApiError:
        logger.exception("/tournaments failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить список турниров, попробуйте позже.")
        return

    text, markup = build_tournaments_list_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["tournament"])
def handle_tournament_detail(message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        bot.send_message(message.chat.id, "Использование: <code>/tournament &lt;id&gt;</code>")
        return
    tournament_id = int(parts[1].strip())

    try:
        data = get_tournament_detail(api_client, tournament_id)
    except ApiNotFound:
        bot.send_message(message.chat.id, "Турнир не найден.")
        return
    except ApiError:
        logger.exception("/tournament failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить турнир, попробуйте позже.")
        return

    text, markup = build_tournament_detail_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)
