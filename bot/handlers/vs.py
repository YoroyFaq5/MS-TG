import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.profile import compare
from bot.api_client.endpoints.players import search_players
from bot.api_client.endpoints.ratings import get_ratings
from bot.presenters.profile import build_not_linked_message
from bot.presenters.vs import build_vs_message, build_vs_picker_message, build_vs_search_prompt_message, build_vs_search_results_message
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb
from bot.ui import error_state
from bot import storage

logger = logging.getLogger(__name__)

SCENARIO = "vs_search"


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
        bot.send_message(message.chat.id, error_state("Не удалось получить список игроков."))
        return

    text, markup = build_vs_picker_message(data["items"], player_id)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "vs", "hub"))
@guarded_callback(bot)
def handle_vs_hub_callback(call) -> None:
    storage.clear_fsm_state(call.message.chat.id)
    telegram_id = call.from_user.id
    player_id = resolve_player_id(api_client, telegram_id)
    if player_id is None:
        text, markup = build_not_linked_message()
    else:
        data = get_ratings(api_client, scope="global", page=1, per_page=8)
        text, markup = build_vs_picker_message(data["items"], player_id)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "vs", "search"))
@guarded_callback(bot)
def handle_vs_search_start(call) -> None:
    storage.set_fsm_state(call.message.chat.id, SCENARIO, "await_query")
    text, markup = build_vs_search_prompt_message()
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.message_handler(
    func=lambda m: (storage.get_fsm_state(m.chat.id) or {}).get("scenario") == SCENARIO,
    content_types=["text"],
)
def handle_vs_search_text(message) -> None:
    query = (message.text or "").strip()
    storage.clear_fsm_state(message.chat.id)
    if not query:
        return
    try:
        candidates = search_players(api_client, query)
    except ApiError:
        bot.send_message(message.chat.id, error_state("Поиск временно недоступен."))
        return
    my_player_id = resolve_player_id(api_client, message.from_user.id)
    candidates = [c for c in candidates if c["id"] != my_player_id][:8]
    text, markup = build_vs_search_results_message(candidates, query)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("vs:"))
@guarded_callback(bot)
def handle_vs_callback(call) -> None:
    opponent_id = int(call.data.split(":", 1)[1])
    telegram_id = call.from_user.id

    player_id = resolve_player_id(api_client, telegram_id)
    if player_id is None:
        text, _ = build_not_linked_message()
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text)
        return
    try:
        data = compare(api_client, telegram_id, opponent_id)
    except ApiNotFound:
        bot.answer_callback_query(call.id, "Игрок не найден.")
        return

    text, markup = build_vs_message(data)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)
