from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc


def build_balance_message(balance: float, history_items: list) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [f"💰 Баланс: <b>{i18n.fmt_coins(balance)}</b>", ""]
    if history_items:
        lines.append("Последние операции:")
        for tx in history_items:
            date = i18n.fmt_date_only(tx["created_at"])
            lines.append(f"{date}: {i18n.fmt_signed_coins(tx['amount'])} — {esc(tx.get('reason') or '')}")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔄 Обновить", callback_data=cb("profile", "balance")))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("profile", "open"))
