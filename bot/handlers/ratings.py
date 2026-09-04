import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.ratings import get_ratings
from bot.presenters.ratings import build_ratings_message
from bot.presenters.seasons import build_ratings_hub_message
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import error_state

logger = logging.getLogger(__name__)


def open_ratings_hub(chat_id: int, message_id=None) -> None:
    text, markup = build_ratings_hub_message()
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)


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
        bot.send_message(message.chat.id, error_state("Не удалось получить рейтинг."))
        return

    text, markup = build_ratings_message(data, scope="global")
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "rating", "hub"))
@guarded_callback(bot, answer_immediately=True)
def handle_rating_hub_callback(call) -> None:
    open_ratings_hub(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "rating", "global"))
@guarded_callback(bot, answer_immediately=True)
def handle_rating_page_callback(call) -> None:
    _, _, page = parse_cb(call.data)
    data = get_ratings(api_client, scope="global", page=int(page), per_page=10)
    text, markup = build_ratings_message(data, scope="global")
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
