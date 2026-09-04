"""
Main menu — inline hierarchical navigation (see PROMPT_FOR_CLAUDE_BOT.md
section 2). A single compact Reply Keyboard button ("🏠 Меню") is the only
non-inline UI element left in the whole bot; every actual screen after that
is an inline keyboard editing the same message in place.
"""
from typing import Tuple

from telebot import types

from bot.keyboards.nav import cb

# (section key, button label, short hub subtitle)
MAIN_SECTIONS = [
    ("profile", "👤 Мой кабинет"),
    ("rating", "🏆 Рейтинги"),
    ("tourn", "🎮 Турниры"),
    ("fantasy", "🎯 Фэнтези"),
    ("shop", "🛍 Магазин"),
    ("inv", "🎒 Инвентарь"),
    ("gift", "🎁 Подарки"),
    ("vs", "🆚 Сравнить игроков"),
    ("notif", "🔔 Уведомления"),
]


def build_reply_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🏠 Меню")
    return markup


def build_main_menu_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🏠 <b>Главное меню MafiaStyle</b>\n\nВыбери раздел:"
    markup = types.InlineKeyboardMarkup()
    for i in range(0, len(MAIN_SECTIONS), 2):
        chunk = MAIN_SECTIONS[i:i + 2]
        markup.row(*[
            types.InlineKeyboardButton(label, callback_data=cb("nav", "open", key))
            for key, label in chunk
        ])
    return text, markup


def build_private_help_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    """/help in a private chat — same command name as the group version
    (CLAUDE_TASK_BOT_RU_GROUPS.md, раздел 4), different content: the full
    personal command list instead of the short public one."""
    text = (
        "🤖 <b>Команды личного чата</b>\n\n"
        "/start — открыть меню\n"
        "/me — профиль\n"
        "/stats — статистика\n"
        "/balance — баланс\n"
        "/history — история игр\n"
        "/rating — рейтинг\n"
        "/tournaments — турниры\n"
        "/compare &lt;ник 1&gt; | &lt;ник 2&gt; — сравнить игроков\n"
        "/achievements — достижения\n"
        "/titles — титулы\n"
        "/unlink — отвязать аккаунт\n\n"
        "Ниже — главное меню со всеми разделами, включая Фэнтези, "
        "магазин, инвентарь и подарки."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Открыть меню", callback_data=cb("nav", "home")))
    return text, markup
