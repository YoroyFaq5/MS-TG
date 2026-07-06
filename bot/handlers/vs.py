import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.profile import compare
from bot.api_client.endpoints.ratings import get_ratings
from bot.presenters.profile import build_not_linked_message
from bot.presenters.vs import build_vs_message, build_vs_picker_message
from bot.services.linking_service import resolve_player_id

logger = logging.getLogger(__name__)


def handle_vs_menu(message) -> None:
    telegram_id = message.from_user.id
    try:
        player_id = resolve_player_id(api_client, telegram_id)
        if player_id is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = get_ratings(api_client, scope="global", page=1, per_page=8)
    except ApiError:
        logger.exception("Кто круче menu failed")
        bot.send_message(message.chat.id, "⚠️ Не удалось получить список игроков, попробуйте позже.")
        return

    text, markup = build_vs_picker_message(data["items"], player_id)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("vs:"))
def handle_vs_callback(call) -> None:
    opponent_id = int(call.data.split(":", 1)[1])
    telegram_id = call.from_user.id

    try:
        player_id = resolve_player_id(api_client, telegram_id)
        if player_id is None:
            text, _ = build_not_linked_message()
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, text)
            return
        data = compare(api_client, telegram_id, opponent_id)
    except ApiNotFound:
        bot.answer_callback_query(call.id, "Игрок не найден.")
        return
    except ApiError:
        logger.exception("Кто круче callback failed")
        bot.answer_callback_query(call.id, "⚠️ Не удалось сравнить, попробуйте позже.")
        return

    text, markup = build_vs_message(data)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)
