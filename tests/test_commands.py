"""
Telegram command registration (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 4):
different scopes/lists for private vs. group chats, idempotent (a
no-op run must not call setMyCommands again).
"""
from unittest.mock import MagicMock

from telebot import types

from bot.commands import register_commands, PRIVATE_COMMANDS, GROUP_COMMANDS


def test_register_commands_sets_both_scopes_when_empty():
    bot = MagicMock()
    bot.get_my_commands.return_value = []

    result = register_commands(bot)

    assert result == {"private": "updated", "group": "updated"}
    assert bot.set_my_commands.call_count == 2
    scopes = [call.kwargs["scope"].__class__.__name__ for call in bot.set_my_commands.call_args_list]
    assert "BotCommandScopeAllPrivateChats" in scopes
    assert "BotCommandScopeAllGroupChats" in scopes


def test_register_commands_is_idempotent_when_unchanged():
    bot = MagicMock()

    def fake_get_my_commands(scope=None):
        if isinstance(scope, types.BotCommandScopeAllPrivateChats):
            return [types.BotCommand(c, d) for c, d in PRIVATE_COMMANDS]
        return [types.BotCommand(c, d) for c, d in GROUP_COMMANDS]

    bot.get_my_commands.side_effect = fake_get_my_commands

    result = register_commands(bot)

    assert result == {"private": "unchanged", "group": "unchanged"}
    bot.set_my_commands.assert_not_called()


def test_group_commands_cover_every_required_public_command():
    names = {c for c, _ in GROUP_COMMANDS}
    for required in ("top", "season", "tournaments", "player", "compare", "game", "help"):
        assert required in names


def test_group_commands_never_include_personal_command_names():
    names = {c for c, _ in GROUP_COMMANDS}
    for forbidden in ("me", "balance", "unlink", "start"):
        assert forbidden not in names


def test_all_command_descriptions_are_russian_non_empty():
    for _, description in PRIVATE_COMMANDS + GROUP_COMMANDS:
        assert description
        assert not description.isascii(), f"description looks untranslated: {description!r}"
