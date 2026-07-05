from typing import Optional, Tuple

from telebot import types


def build_balance_message(balance: float, history_items: list) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    lines = [f"💰 Баланс: <b>{round(balance, 2)}</b>", ""]
    if history_items:
        lines.append("Последние операции:")
        for tx in history_items:
            sign = "+" if tx["amount"] >= 0 else ""
            lines.append(f"{tx['created_at'][:10]}: {sign}{tx['amount']:.1f} — {tx.get('reason') or ''}")
    return "\n".join(lines), None
