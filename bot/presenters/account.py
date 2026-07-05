from typing import Optional, Tuple

from telebot import types


def build_unlink_confirm_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = (
        "🔓 Отвязать Telegram-аккаунт от сайта?\n\n"
        "Вы перестанете получать уведомления, и команды профиля не будут "
        "работать, пока не привяжете аккаунт заново на сайте."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да, отвязать", callback_data="unlink_confirm"),
        types.InlineKeyboardButton("Отмена", callback_data="unlink_cancel"),
    )
    return text, markup


def build_unlink_done_message() -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    return "Telegram отвязан от аккаунта на сайте.", None


def build_unlink_cancelled_message() -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    return "Отменено — аккаунт остаётся привязан.", None
