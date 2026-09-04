from typing import Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.storage import NOTIFICATION_CATEGORIES


def build_notification_settings_message(prefs: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🔔 <b>Уведомления</b>\n\nВключай/выключай категории по вкусу:"
    markup = types.InlineKeyboardMarkup()
    for key, label in NOTIFICATION_CATEGORIES.items():
        state_icon = "✅" if prefs.get(key, True) else "▫️"
        markup.add(types.InlineKeyboardButton(
            f"{state_icon} {label}", callback_data=cb("notif", "toggle", key),
        ))
    return text, add_nav_footer(markup)
