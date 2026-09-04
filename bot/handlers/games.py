import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiNotFound
from bot.api_client.endpoints.games import get_game_detail
from bot.presenters.games import build_game_detail_message
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import stale_state

logger = logging.getLogger(__name__)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "game", "detail"))
@guarded_callback(bot)
def handle_game_detail_callback(call) -> None:
    _, _, game_id = parse_cb(call.data)
    try:
        data = get_game_detail(api_client, int(game_id))
    except ApiNotFound:
        bot.edit_message_text(
            stale_state("Игра больше не найдена."), call.message.chat.id, call.message.message_id,
        )
        bot.answer_callback_query(call.id)
        return

    text, markup = build_game_detail_message(data)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)
