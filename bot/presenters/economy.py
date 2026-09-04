from typing import Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc


def build_balance_message(balance: float, history_items: list) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [f"💰 Баланс: <b>{round(balance, 2)}</b>", ""]
    if history_items:
        lines.append("Последние операции:")
        for tx in history_items:
            sign = "+" if tx["amount"] >= 0 else ""
            lines.append(f"{tx['created_at'][:10]}: {sign}{tx['amount']:.1f} — {esc(tx.get('reason') or '')}")
    return "\n".join(lines), add_nav_footer(types.InlineKeyboardMarkup(), back_target=cb("profile", "open"))
