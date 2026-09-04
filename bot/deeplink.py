"""
Deep-link payload resolution for `/start <payload>` (Telegram restricts the
payload charset to `[A-Za-z0-9_-]`, hence the underscore-separated, no-colon
format here — different from the `v1:domain:action:...` callback_data
scheme used everywhere else).

Links posted on the main site should point at
`https://t.me/<bot_username>?start=<payload>` using these exact prefixes so
opening the bot cold lands the user on the right screen instead of just the
main menu. Each resolver returns a (text, markup) tuple ready to send, or
None if the payload doesn't parse / the target no longer exists — the
caller (handlers/start.py) falls back to the plain main menu in that case.

Supported prefixes:
    g<game_id>              — a specific game's card
    t<tournament_id>        — a tournament (series-aware, same as tapping
                               it from the list)
    ev<tournament_id>_<series_id> — one series-tournament evening
    fd<tournament_id>       — Fantasy hub for a whole tournament
    fs<tournament_id>_<series_id> — Fantasy hub for one series evening
    season<season_id>       — a season's rating table
    gift                    — gifts inbox
"""
from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

from telebot import types

logger = logging.getLogger(__name__)

_INT = r"(\d+)"
_PATTERNS = {
    "game": re.compile(rf"^g{_INT}$"),
    "tournament": re.compile(rf"^t{_INT}$"),
    "evening": re.compile(rf"^ev{_INT}_{_INT}$"),
    "fantasy_tournament": re.compile(rf"^fd{_INT}$"),
    "fantasy_series": re.compile(rf"^fs{_INT}_{_INT}$"),
    "season": re.compile(rf"^season{_INT}$"),
    "gift": re.compile(r"^gift$"),
}


def _game(game_id: int) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    from bot.telegram_bot import api_client
    from bot.api_client.exceptions import ApiError
    from bot.api_client.endpoints.games import get_game_detail
    from bot.presenters.games import build_game_detail_message

    try:
        data = get_game_detail(api_client, game_id)
    except ApiError:
        return None
    return build_game_detail_message(data)


def _tournament(tournament_id: int) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    from bot.telegram_bot import api_client
    from bot.api_client.exceptions import ApiError
    from bot.api_client.endpoints.tournaments import get_tournament_detail
    from bot.presenters.tournaments import build_tournament_detail_message

    try:
        data = get_tournament_detail(api_client, tournament_id)
    except ApiError:
        return None
    if data.get("series_tournament_id"):
        return _series_tournament(data["series_tournament_id"])
    return build_tournament_detail_message(data)


def _series_tournament(series_tournament_id: int) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    from bot.telegram_bot import api_client
    from bot.api_client.exceptions import ApiError
    from bot.api_client.endpoints.series_tournaments import get_series_tournament_detail
    from bot.presenters.tournaments import build_series_tournament_message

    try:
        data = get_series_tournament_detail(api_client, series_tournament_id)
    except ApiError:
        return None
    return build_series_tournament_message(data)


def _evening(tournament_id: int, series_id: int) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    from bot.telegram_bot import api_client
    from bot.api_client.exceptions import ApiError
    from bot.api_client.endpoints.series_tournaments import get_series_shortcut, get_series_evening_detail
    from bot.presenters.tournaments import build_series_evening_message

    try:
        shortcut = get_series_shortcut(api_client, series_id)
        data = get_series_evening_detail(api_client, shortcut["series_tournament_id"], series_id)
    except ApiError:
        return None
    return build_series_evening_message(data)


def _fantasy(
    tournament_id: int, telegram_id: int, series_id: int = 0,
) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    from bot.telegram_bot import api_client
    from bot.api_client.exceptions import ApiError, ApiNotFound
    from bot.api_client.endpoints.fantasy import get_my_draft
    from bot.api_client.endpoints.tournaments import get_tournament_detail
    from bot.presenters.fantasy import build_fantasy_hub_message
    from bot.services.linking_service import resolve_player_id

    try:
        name = get_tournament_detail(api_client, tournament_id)["tournament"]["name"]
    except ApiError:
        return None
    draft = None
    if resolve_player_id(api_client, telegram_id) is not None:
        try:
            draft = get_my_draft(api_client, telegram_id, tournament_id, series_id or None, False)
        except (ApiError, ApiNotFound):
            draft = None
    return build_fantasy_hub_message(tournament_id, series_id, False, name, draft)


def _season(season_id: int) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    from bot.telegram_bot import api_client
    from bot.api_client.exceptions import ApiError
    from bot.api_client.endpoints.seasons import get_season_detail
    from bot.presenters.seasons import build_season_detail_message

    try:
        data = get_season_detail(api_client, season_id)
    except ApiError:
        return None
    return build_season_detail_message(data)


def _gift() -> Tuple[str, types.InlineKeyboardMarkup]:
    from bot.presenters.gifts import build_gifts_hub_message
    return build_gifts_hub_message()


def resolve_deep_link(payload: str, telegram_id: int) -> Optional[Tuple[str, types.InlineKeyboardMarkup]]:
    payload = (payload or "").strip()
    if not payload:
        return None

    if _PATTERNS["gift"].match(payload):
        return _gift()

    m = _PATTERNS["game"].match(payload)
    if m:
        return _game(int(m.group(1)))

    m = _PATTERNS["tournament"].match(payload)
    if m:
        return _tournament(int(m.group(1)))

    m = _PATTERNS["evening"].match(payload)
    if m:
        return _evening(int(m.group(1)), int(m.group(2)))

    m = _PATTERNS["fantasy_tournament"].match(payload)
    if m:
        return _fantasy(int(m.group(1)), telegram_id)

    m = _PATTERNS["fantasy_series"].match(payload)
    if m:
        return _fantasy(int(m.group(1)), telegram_id, int(m.group(2)))

    m = _PATTERNS["season"].match(payload)
    if m:
        return _season(int(m.group(1)))

    logger.info("Unrecognized deep-link payload: %r", payload)
    return None
