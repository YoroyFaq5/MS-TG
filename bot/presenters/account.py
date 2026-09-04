from typing import Optional, Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc


def build_unlink_confirm_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = (
        "🔓 Отвязать Telegram-аккаунт от сайта?\n\n"
        "Вы перестанете получать уведомления, и команды профиля не будут "
        "работать, пока не привяжете аккаунт заново на сайте."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да, отвязать", callback_data=cb("account", "unlink-yes")),
        types.InlineKeyboardButton("Отмена", callback_data=cb("account", "unlink-no")),
    )
    return text, markup


def build_unlink_done_message() -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    return "Telegram отвязан от аккаунта на сайте.", None


def build_unlink_cancelled_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    return "Отменено — аккаунт остаётся привязан.", add_nav_footer(
        types.InlineKeyboardMarkup(), back_target=cb("profile", "open"),
    )


def build_account_status_message(display_name: str) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    text = f"⚙️ Привязан аккаунт: <b>{esc(display_name)}</b>."
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔓 Отвязать аккаунт", callback_data=cb("account", "unlink-confirm")))
    return text, add_nav_footer(markup, back_target=cb("profile", "open"))
