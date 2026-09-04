"""
/compare — two forms, same command name (CLAUDE_TASK_BOT_RU_GROUPS.md,
раздел 3 и 5):
  - `/compare <ник 1> | <ник 2>` — public, name-based, safe in groups and
    private alike (no personal data, no telegram-account linkage needed);
  - `/compare <id>` — the ORIGINAL private-only shortcut ("me vs a known
    player id"), kept working for old muscle memory but deprecated: it
    depends on the caller's own linked account, so it stays private-only
    and is never advertised in /help any more.
"""
import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.api_client.endpoints.profile import compare
from bot.api_client.endpoints.players import search_players, compare_players
from bot.presenters.profile import build_not_linked_message
from bot.presenters.vs import build_vs_message
from bot.presenters.group import (
    build_group_compare_message, build_usage_error_message, build_rate_limited_message,
)
from bot.services.linking_service import resolve_player_id
from bot.chat_policy import is_group
from bot.ratelimit import check_group_command_rate_limit
from bot.ui import esc, error_state

logger = logging.getLogger(__name__)

_USAGE = "/compare &lt;ник 1&gt; | &lt;ник 2&gt;"


@bot.message_handler(commands=["compare"])
def handle_compare(message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    if "|" in arg:
        _handle_name_compare(message, arg)
        return
    if arg.isdigit():
        _handle_legacy_id_compare(message, int(arg))
        return
    bot.send_message(message.chat.id, build_usage_error_message(_USAGE))


def _handle_legacy_id_compare(message, opponent_id: int) -> None:
    """Deprecated: compares the CALLER's own linked profile against a
    known player id. Meaningless without a linked account, so it stays
    private-only rather than telling a group user to go link one."""
    if is_group(message.chat.type):
        bot.send_message(message.chat.id, build_usage_error_message(_USAGE))
        return

    telegram_id = message.from_user.id
    try:
        if resolve_player_id(api_client, telegram_id) is None:
            text, markup = build_not_linked_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return
        data = compare(api_client, telegram_id, opponent_id)
    except ApiNotFound:
        bot.send_message(message.chat.id, "Игрок с таким id не найден.")
        return
    except ApiError:
        logger.exception("/compare (legacy id) failed")
        bot.send_message(message.chat.id, error_state("Не удалось сравнить, попробуйте позже."))
        return

    text, markup = build_vs_message(data)
    bot.send_message(message.chat.id, text, reply_markup=markup)


def _resolve_one(name: str):
    """Best-effort name -> player id. Returns (player_id, note) on success
    (note is '' unless the match was ambiguous) or (None, message) on
    failure — deliberately picks the first search hit on ambiguity rather
    than running a second interactive round-trip, since /compare already
    takes two names in one message; /player <ник> is offered for anyone
    who needs to disambiguate properly."""
    try:
        candidates = search_players(api_client, name)
    except ApiError:
        return None, error_state("Не удалось найти игрока.")
    if not candidates:
        return None, f"Игрок «{esc(name)}» не найден."
    if len(candidates) == 1:
        return candidates[0]["id"], ""
    chosen = candidates[0]
    note = (
        f"По «{esc(name)}» нашлось несколько игроков — сравниваю с "
        f"{esc(chosen['display_name'])}. Если это не тот, уточни ник через /player."
    )
    return chosen["id"], note


def _handle_name_compare(message, arg: str) -> None:
    if is_group(message.chat.type):
        allowed, should_warn = check_group_command_rate_limit(message.chat.id, message.from_user.id)
        if not allowed:
            if should_warn:
                bot.send_message(message.chat.id, build_rate_limited_message())
            return

    name_a, _, name_b = arg.partition("|")
    name_a, name_b = name_a.strip(), name_b.strip()
    if not name_a or not name_b:
        bot.send_message(message.chat.id, build_usage_error_message(_USAGE))
        return

    id_a, info_a = _resolve_one(name_a)
    if id_a is None:
        bot.send_message(message.chat.id, info_a)
        return
    id_b, info_b = _resolve_one(name_b)
    if id_b is None:
        bot.send_message(message.chat.id, info_b)
        return
    if id_a == id_b:
        bot.send_message(message.chat.id, "Это один и тот же игрок — сравнивать не с кем.")
        return

    note = "\n".join(n for n in (info_a, info_b) if n)
    try:
        data = compare_players(api_client, id_a, id_b)
    except ApiNotFound:
        bot.send_message(message.chat.id, "Не удалось сравнить — один из игроков не найден.")
        return
    except ApiError:
        logger.exception("/compare (name) failed")
        bot.send_message(message.chat.id, error_state("Не удалось сравнить, попробуйте позже."))
        return

    text, markup = build_group_compare_message(data, note)
    bot.send_message(message.chat.id, text, reply_markup=markup)
