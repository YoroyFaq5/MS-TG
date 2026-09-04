"""
Public group-chat commands (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 3):
/top, /season, /player, /game, /help. (/tournaments and /compare share
their command name with an existing private feature and are branched
in-place in bot/handlers/tournaments.py and bot/handlers/compare.py
instead of living here.)

All of these also work in a private chat with identical, fully-public
output — there is nothing personal in any of them, so there is no reason
to withhold them there. Only the group/supergroup antispam rate limit
(bot/ratelimit.py) is conditional on chat type.
"""
import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.ratings import get_ratings
from bot.api_client.endpoints.seasons import get_current_season, get_season_detail
from bot.api_client.endpoints.players import search_players, get_player
from bot.api_client.endpoints.games import get_game_detail
from bot.presenters.group import (
    build_top_message, build_group_season_message, build_group_player_card_message,
    build_player_disambiguation_message, build_player_not_found_message,
    build_group_game_message, build_group_help_message, build_rate_limited_message,
    build_usage_error_message,
)
from bot.presenters.menu import build_private_help_message
from bot.presenters.seasons import build_season_summary_message
from bot.chat_policy import is_group
from bot.ratelimit import check_group_command_rate_limit
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import error_state

logger = logging.getLogger(__name__)


def _rate_limited(message) -> bool:
    """True (and the caller must stop) only in a group/supergroup that has
    exceeded its window; private chats are never limited here."""
    if not is_group(message.chat.type):
        return False
    allowed, should_warn = check_group_command_rate_limit(message.chat.id, message.from_user.id)
    if allowed:
        return False
    if should_warn:
        bot.send_message(message.chat.id, build_rate_limited_message())
    return True


@bot.message_handler(commands=["top"])
def handle_top(message) -> None:
    if _rate_limited(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    limit = 10
    if len(parts) > 1 and parts[1].strip().isdigit():
        limit = max(3, min(10, int(parts[1].strip())))

    try:
        data = get_ratings(api_client, scope="global", page=1, per_page=limit)
    except ApiError:
        logger.exception("/top failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить рейтинг."))
        return

    text, markup = build_top_message(data, limit)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["season"])
def handle_season(message) -> None:
    if is_group(message.chat.type):
        if _rate_limited(message):
            return
        try:
            season = get_current_season(api_client)
            top5, min_games = [], 0
            if season:
                detail = get_season_detail(api_client, season["id"], page=1, per_page=5)
                top5 = detail["ratings"]["items"]
                min_games = detail["min_games_for_top5"]
        except ApiError:
            logger.exception("group /season failed")
            bot.send_message(message.chat.id, error_state("Не удалось получить данные сезона."))
            return
        text, markup = build_group_season_message(season, top5, min_games)
        bot.send_message(message.chat.id, text, reply_markup=markup)
        return

    try:
        season = get_current_season(api_client)
    except ApiError:
        logger.exception("/season failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить данные сезона."))
        return
    text, markup = build_season_summary_message(season)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["player"])
def handle_player(message) -> None:
    if _rate_limited(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    query = parts[1].strip() if len(parts) > 1 else ""
    if not query:
        bot.send_message(message.chat.id, build_usage_error_message("/player &lt;ник&gt;"))
        return
    _lookup_and_send_player(message.chat.id, query)


def _lookup_and_send_player(chat_id: int, query: str) -> None:
    try:
        candidates = search_players(api_client, query)
    except ApiError:
        logger.exception("/player search failed")
        bot.send_message(chat_id, error_state("Не удалось найти игрока."))
        return
    if not candidates:
        bot.send_message(chat_id, build_player_not_found_message(query))
        return
    if len(candidates) == 1:
        _send_player_card(chat_id, candidates[0]["id"])
        return
    text, markup = build_player_disambiguation_message(candidates, query)
    bot.send_message(chat_id, text, reply_markup=markup)


def _send_player_card(chat_id: int, player_id: int) -> None:
    try:
        player = get_player(api_client, player_id)
    except ApiNotFound:
        bot.send_message(chat_id, "Игрок не найден.")
        return
    except ApiError:
        logger.exception("/player detail failed")
        bot.send_message(chat_id, error_state("Не удалось получить карточку игрока."))
        return
    text, markup = build_group_player_card_message(player)
    bot.send_message(chat_id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "gplayer", "show"))
@guarded_callback(bot, answer_immediately=True)
def handle_gplayer_show_callback(call) -> None:
    """No private_only here on purpose: this just re-runs the same public
    /player card lookup for a fixed id chosen from a disambiguation list —
    identical public output no matter who taps it, in any chat type."""
    _, _, player_id = parse_cb(call.data)
    _send_player_card(call.message.chat.id, int(player_id))


@bot.message_handler(commands=["game"])
def handle_game(message) -> None:
    if _rate_limited(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    if not arg.isdigit():
        bot.send_message(message.chat.id, build_usage_error_message("/game &lt;номер&gt;"))
        return

    try:
        data = get_game_detail(api_client, int(arg))
    except ApiNotFound:
        bot.send_message(message.chat.id, "Игра с таким номером не найдена.")
        return
    except ApiError:
        logger.exception("/game failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить игру."))
        return

    text, markup = build_group_game_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["help"])
def handle_help(message) -> None:
    if is_group(message.chat.type):
        text, markup = build_group_help_message()
    else:
        text, markup = build_private_help_message()
    bot.send_message(message.chat.id, text, reply_markup=markup)
