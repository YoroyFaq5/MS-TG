import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.tournaments import get_tournaments, get_tournament_detail
from bot.api_client.endpoints.series_tournaments import get_series_tournament_detail, get_series_evening_detail
from bot.presenters.tournaments import (
    build_tournaments_list_message, build_tournament_detail_message,
    build_series_tournament_message, build_series_evening_message,
)
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import error_state, stale_state
from bot.chat_policy import is_group
from bot.ratelimit import check_group_command_rate_limit
from bot.presenters.group import build_group_tournaments_message, build_rate_limited_message

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"pending", "active", "finished"}


def open_tournaments_list(chat_id: int, message_id=None, status=None, page: int = 1) -> None:
    data = get_tournaments(api_client, status=status, page=page, per_page=8)
    text, markup = build_tournaments_list_message(data, status=status)
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)


def _handle_group_tournaments(message) -> None:
    """Compact, non-paginated public /tournaments for group chats
    (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 3) — same command name as the
    private rich list, different (safe, short) behaviour."""
    allowed, should_warn = check_group_command_rate_limit(message.chat.id, message.from_user.id)
    if not allowed:
        if should_warn:
            bot.send_message(message.chat.id, build_rate_limited_message())
        return
    try:
        active = get_tournaments(api_client, status="active", per_page=5)["items"]
        pending = get_tournaments(api_client, status="pending", per_page=5)["items"] if len(active) < 5 else []
    except ApiError:
        logger.exception("group /tournaments failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить список турниров."))
        return
    combined = (active + pending)[:5]
    text, markup = build_group_tournaments_message(combined)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=["tournaments"])
def handle_tournaments(message) -> None:
    if is_group(message.chat.type):
        _handle_group_tournaments(message)
        return

    parts = (message.text or "").split(maxsplit=1)
    status = parts[1].strip() if len(parts) > 1 and parts[1].strip() in _VALID_STATUSES else None
    try:
        open_tournaments_list(message.chat.id, status=status)
    except ApiError:
        logger.exception("/tournaments failed")
        bot.send_message(message.chat.id, error_state("Не удалось получить список турниров."))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "tourn", "list"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_tournament_list_callback(call) -> None:
    _, _, status_raw, page = parse_cb(call.data)
    status = None if status_raw == "-" else status_raw
    open_tournaments_list(call.message.chat.id, call.message.message_id, status=status, page=int(page))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "tourn", "open"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_tournament_open_callback(call) -> None:
    _, _, tournament_id, series_tournament_id = parse_cb(call.data)
    tournament_id, series_tournament_id = int(tournament_id), int(series_tournament_id)
    telegram_id = call.from_user.id

    try:
        if series_tournament_id:
            data = get_series_tournament_detail(api_client, series_tournament_id)
            text, markup = build_series_tournament_message(data)
        else:
            data = get_tournament_detail(api_client, tournament_id, telegram_id=telegram_id)
            text, markup = build_tournament_detail_message(data)
    except ApiNotFound:
        bot.edit_message_text(
            stale_state("Турнир больше не существует."), call.message.chat.id, call.message.message_id,
        )
        return

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "tourn", "series-evening"))
@guarded_callback(bot, answer_immediately=True, private_only=True)
def handle_series_evening_callback(call) -> None:
    _, _, series_tournament_id, series_id = parse_cb(call.data)
    try:
        data = get_series_evening_detail(api_client, int(series_tournament_id), int(series_id))
    except ApiNotFound:
        bot.edit_message_text(
            stale_state("Этот вечер больше не существует."), call.message.chat.id, call.message.message_id,
        )
        return

    text, markup = build_series_evening_message(data)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
