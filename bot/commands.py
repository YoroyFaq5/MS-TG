"""
Telegram command registration (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 4) —
`setMyCommands` with two different scopes so the client shows a different
"/" menu in a private chat vs. a group, in Russian. Called explicitly (via
`flask set-commands`, see run.py) rather than on every webhook update:
Telegram itself caches these per scope and only needs a call when the list
actually changes, so doing it per-update would be both wasteful and racy
under concurrent webhook workers.
"""
from __future__ import annotations

import logging

from telebot import types

logger = logging.getLogger(__name__)

PRIVATE_COMMANDS = [
    ("start", "Открыть меню"),
    ("help", "Список команд"),
]

GROUP_COMMANDS = [
    ("top", "Топ рейтинга клуба"),
    ("season", "Текущий сезон"),
    ("tournaments", "Активные и ближайшие турниры"),
    ("player", "Карточка игрока по нику"),
    ("compare", "Сравнить двух игроков"),
    ("game", "Карточка завершённой игры"),
    ("help", "Список команд"),
]


def _as_bot_commands(pairs: list[tuple[str, str]]) -> list[types.BotCommand]:
    return [types.BotCommand(cmd, desc) for cmd, desc in pairs]


def _needs_update(current: list[types.BotCommand], desired: list[tuple[str, str]]) -> bool:
    current_pairs = [(c.command, c.description) for c in current]
    return current_pairs != desired


def register_commands(bot) -> dict:
    """Idempotent: only calls setMyCommands for a scope whose list has
    actually drifted from what's already registered. Returns a small
    summary dict for the CLI command to print."""
    result = {}

    private_scope = types.BotCommandScopeAllPrivateChats()
    current_private = bot.get_my_commands(scope=private_scope) or []
    if _needs_update(current_private, PRIVATE_COMMANDS):
        bot.set_my_commands(_as_bot_commands(PRIVATE_COMMANDS), scope=private_scope)
        result["private"] = "updated"
    else:
        result["private"] = "unchanged"

    group_scope = types.BotCommandScopeAllGroupChats()
    current_group = bot.get_my_commands(scope=group_scope) or []
    if _needs_update(current_group, GROUP_COMMANDS):
        bot.set_my_commands(_as_bot_commands(GROUP_COMMANDS), scope=group_scope)
        result["group"] = "updated"
    else:
        result["group"] = "unchanged"

    logger.info("Telegram command registration: %s", result)
    return result
