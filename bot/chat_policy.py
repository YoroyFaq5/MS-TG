"""
Private-vs-group policy (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 2) —
единственное место, где бот решает, разрешён ли персональный/изменяющий
данные сценарий в данном чате. Telegram присылает три типа чата:
`private`, `group`, `supergroup` (плюс `channel`, которого этот бот не
поддерживает — трактуется как группа: тоже не личный чат).

Персональные данные (баланс, инвентарь, подарки, настройки, Telegram ID)
и любые мутирующие действия (покупка, Фэнтези-драфт, отвязка аккаунта,
свободный ввод в FSM) доступны только в private — см.
guarded_callback(..., private_only=True) в bot/dispatch.py и
require_private_message() ниже для команд-сообщений.
"""
from __future__ import annotations

import functools
import logging

from telebot import types

from bot.bot_identity import bot_url

logger = logging.getLogger(__name__)

PRIVATE_ONLY_TEXT = "Эта функция доступна только в личном чате."
PRIVATE_ONLY_TOAST = "⚠️ Доступно только в личном чате"


def is_private(chat_type: str) -> bool:
    return chat_type == "private"


def is_group(chat_type: str) -> bool:
    return chat_type in ("group", "supergroup")


def open_bot_button() -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton("🤖 Открыть бота", url=bot_url())


def private_only_message() -> tuple[str, types.InlineKeyboardMarkup]:
    markup = types.InlineKeyboardMarkup()
    markup.add(open_bot_button())
    return PRIVATE_ONLY_TEXT, markup


def require_private_message(handler):
    """Decorator for @bot.message_handler targets that must not run in a
    group — sends the short "личный чат"-only notice with an "Открыть
    бота" button instead of the real handler."""

    @functools.wraps(handler)
    def wrapped(message, *args, **kwargs):
        from bot.telegram_bot import bot

        if not is_private(message.chat.type):
            text, markup = private_only_message()
            bot.send_message(message.chat.id, text, reply_markup=markup)
            return None
        return handler(message, *args, **kwargs)

    return wrapped
