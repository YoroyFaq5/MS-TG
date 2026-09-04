import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.seasons import (
    get_current_season, get_seasons, get_season_detail, get_my_place, get_season_winners,
)
from bot.presenters.seasons import (
    build_season_summary_message, build_seasons_list_message, build_season_detail_message,
    build_my_place_message, build_season_winners_message,
)
from bot.presenters.profile import build_not_linked_message
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb

logger = logging.getLogger(__name__)


def _edit(call, text, markup):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "season", "current"))
@guarded_callback(bot, answer_immediately=True)
def handle_season_current(call) -> None:
    season = get_current_season(api_client)
    _edit(call, *build_season_summary_message(season))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "season", "list"))
@guarded_callback(bot, answer_immediately=True)
def handle_season_list(call) -> None:
    data = get_seasons(api_client)
    _edit(call, *build_seasons_list_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "season", "detail"))
@guarded_callback(bot, answer_immediately=True)
def handle_season_detail(call) -> None:
    _, _, season_id, page = parse_cb(call.data)
    data = get_season_detail(api_client, int(season_id), page=int(page))
    _edit(call, *build_season_detail_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "season", "myplace"))
@guarded_callback(bot, answer_immediately=True)
def handle_season_myplace(call) -> None:
    _, _, season_id = parse_cb(call.data)
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        text, markup = build_not_linked_message()
        _edit(call, text, markup)
        return
    data = get_my_place(api_client, telegram_id, int(season_id))
    _edit(call, *build_my_place_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "season", "myplace-current"))
@guarded_callback(bot, answer_immediately=True)
def handle_season_myplace_current(call) -> None:
    telegram_id = call.from_user.id
    if resolve_player_id(api_client, telegram_id) is None:
        text, markup = build_not_linked_message()
        _edit(call, text, markup)
        return
    season = get_current_season(api_client)
    if not season:
        _edit(call, *build_season_summary_message(None))
        return
    data = get_my_place(api_client, telegram_id, season["id"])
    _edit(call, *build_my_place_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "season", "winners"))
@guarded_callback(bot, answer_immediately=True)
def handle_season_winners(call) -> None:
    _, _, page = parse_cb(call.data)
    data = get_season_winners(api_client, page=int(page))
    _edit(call, *build_season_winners_message(data))
