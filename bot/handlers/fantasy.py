import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.fantasy import (
    get_events, get_history, get_my_draft, get_draft_by_id, create_draft, add_pick, remove_pick,
    cancel_draft, get_leaderboard, get_available,
)
from bot.api_client.endpoints.tournaments import get_tournament_detail
from bot.api_client.endpoints.series_tournaments import get_series_shortcut
from bot.presenters.profile import build_not_linked_message
from bot.presenters.fantasy import (
    build_fantasy_events_message, build_fantasy_hub_message, build_my_draft_message,
    build_cancel_confirm_message, build_available_message, build_leaderboard_message,
    build_history_message,
)
from bot.services.linking_service import resolve_player_id
from bot.dispatch import guarded_callback
from bot.keyboards.nav import is_cb, parse_cb
from bot.ui import error_state

logger = logging.getLogger(__name__)


def _scope_name(tournament_id: int, series_id: int) -> str:
    if series_id:
        shortcut = get_series_shortcut(api_client, series_id)
        return shortcut["series"]["name"]
    detail = get_tournament_detail(api_client, tournament_id)
    return detail["tournament"]["name"]


def _edit(call, text, markup):
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)


def _require_linked(call) -> bool:
    if resolve_player_id(api_client, call.from_user.id) is None:
        text, markup = build_not_linked_message()
        _edit(call, text, markup)
        return False
    return True


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "events"))
@guarded_callback(bot)
def handle_fantasy_events(call) -> None:
    telegram_id = call.from_user.id
    data = get_events(api_client, telegram_id)
    _edit(call, *build_fantasy_events_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "history"))
@guarded_callback(bot)
def handle_fantasy_history(call) -> None:
    telegram_id = call.from_user.id
    if not _require_linked(call):
        return
    parts = parse_cb(call.data)
    page = int(parts[2]) if len(parts) > 2 else 1
    data = get_history(api_client, telegram_id, page=page)
    _edit(call, *build_history_message(data))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "open"))
@guarded_callback(bot)
def handle_fantasy_open(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    telegram_id = call.from_user.id

    name = _scope_name(tournament_id, series_id)
    draft = None
    if resolve_player_id(api_client, telegram_id) is not None:
        try:
            draft = get_my_draft(api_client, telegram_id, tournament_id, series_id or None, is_practice)
        except ApiNotFound:
            draft = None
    _edit(call, *build_fantasy_hub_message(tournament_id, series_id, is_practice, name, draft))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "my"))
@guarded_callback(bot)
def handle_fantasy_my(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    if not _require_linked(call):
        return
    telegram_id = call.from_user.id
    try:
        draft = get_my_draft(api_client, telegram_id, tournament_id, series_id or None, is_practice)
    except ApiNotFound:
        name = _scope_name(tournament_id, series_id)
        _edit(call, *build_fantasy_hub_message(tournament_id, series_id, is_practice, name, None))
        return
    _edit(call, *build_my_draft_message(draft, tournament_id, series_id, is_practice))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "create"))
@guarded_callback(bot, sensitive=True)
def handle_fantasy_create(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    if not _require_linked(call):
        return
    telegram_id = call.from_user.id
    try:
        create_draft(api_client, telegram_id, tournament_id, series_id or None, is_practice)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    draft = get_my_draft(api_client, telegram_id, tournament_id, series_id or None, is_practice)
    text, markup = build_my_draft_message(draft, tournament_id, series_id, is_practice)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Драфт создан ✅")


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "avail"))
@guarded_callback(bot)
def handle_fantasy_avail(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    telegram_id = call.from_user.id
    players = get_available(api_client, telegram_id, tournament_id, series_id or None, is_practice)
    _edit(call, *build_available_message(players, tournament_id, series_id, is_practice))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "pickf"))
@guarded_callback(bot, sensitive=True)
def handle_fantasy_pick_from_available(call) -> None:
    _, _, tournament_id, series_id, is_practice, player_id = parse_cb(call.data)
    tournament_id, series_id, is_practice, player_id = (
        int(tournament_id), int(series_id), bool(int(is_practice)), int(player_id),
    )
    telegram_id = call.from_user.id
    try:
        draft = get_my_draft(api_client, telegram_id, tournament_id, series_id or None, is_practice)
        add_pick(api_client, telegram_id, draft["id"], player_id)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    players = get_available(api_client, telegram_id, tournament_id, series_id or None, is_practice)
    text, markup = build_available_message(players, tournament_id, series_id, is_practice)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Пик добавлен ✅")


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "unpick"))
@guarded_callback(bot, sensitive=True)
def handle_fantasy_unpick(call) -> None:
    _, _, draft_id, player_id = parse_cb(call.data)
    draft_id, player_id = int(draft_id), int(player_id)
    telegram_id = call.from_user.id
    try:
        remove_pick(api_client, telegram_id, draft_id, player_id)
        draft = get_draft_by_id(api_client, telegram_id, draft_id)
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    text, markup = build_my_draft_message(
        draft, draft["tournament_id"], draft.get("tournament_series_id") or 0, draft["is_practice"],
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Пик убран")


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "cancel-confirm"))
@guarded_callback(bot)
def handle_fantasy_cancel_confirm(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    _edit(call, *build_cancel_confirm_message(tournament_id, series_id, is_practice))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "cancel"))
@guarded_callback(bot, sensitive=True)
def handle_fantasy_cancel(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    telegram_id = call.from_user.id
    try:
        draft = get_my_draft(api_client, telegram_id, tournament_id, series_id or None, is_practice)
        cancel_draft(api_client, telegram_id, draft["id"])
    except ApiError as e:
        bot.answer_callback_query(call.id, f"⚠️ {e}", show_alert=True)
        return
    name = _scope_name(tournament_id, series_id)
    text, markup = build_fantasy_hub_message(tournament_id, series_id, is_practice, name, None)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, "Драфт отменён, монеты возвращены")


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "lb"))
@guarded_callback(bot)
def handle_fantasy_leaderboard(call) -> None:
    _, _, tournament_id, series_id, is_practice = parse_cb(call.data)
    tournament_id, series_id, is_practice = int(tournament_id), int(series_id), bool(int(is_practice))
    entries = get_leaderboard(api_client, tournament_id, series_id or None, is_practice=is_practice)
    name = _scope_name(tournament_id, series_id)
    _edit(call, *build_leaderboard_message(entries, name, tournament_id, series_id, is_practice))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "tourn"))
@guarded_callback(bot)
def handle_fantasy_tourn_shortcut(call) -> None:
    """Shortcut used by other screens (tournament detail, notifications) —
    just an alias for opening the paid hub for a whole tournament."""
    _, _, tournament_id = parse_cb(call.data)
    tournament_id = int(tournament_id)
    telegram_id = call.from_user.id
    name = _scope_name(tournament_id, 0)
    draft = None
    if resolve_player_id(api_client, telegram_id) is not None:
        try:
            draft = get_my_draft(api_client, telegram_id, tournament_id, None, False)
        except ApiNotFound:
            draft = None
    _edit(call, *build_fantasy_hub_message(tournament_id, 0, False, name, draft))


@bot.callback_query_handler(func=lambda call: is_cb(call.data, "fantasy", "series"))
@guarded_callback(bot)
def handle_fantasy_series_shortcut(call) -> None:
    _, _, tournament_id, series_id = parse_cb(call.data)
    tournament_id, series_id = int(tournament_id), int(series_id)
    telegram_id = call.from_user.id
    name = _scope_name(tournament_id, series_id)
    draft = None
    if resolve_player_id(api_client, telegram_id) is not None:
        try:
            draft = get_my_draft(api_client, telegram_id, tournament_id, series_id, False)
        except ApiNotFound:
            draft = None
    _edit(call, *build_fantasy_hub_message(tournament_id, series_id, False, name, draft))
