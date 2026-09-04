from typing import Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import truncate

ROLE_ICONS = {"civilian": "👤", "mafia": "🔫", "don": "🎩", "sheriff": "🔍"}


def build_history_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    lines = [f"📜 <b>История игр</b> — стр. {page}", ""]
    markup = types.InlineKeyboardMarkup()
    for item in items:
        slot, game = item["slot"], item["game"]
        date = game["played_at"][:10]
        result_icon = "✅" if item["won"] else "❌"
        role_icon = ROLE_ICONS.get(slot["role"], "")
        pu_mark = " 🎯" if slot["is_pu"] else ""
        lines.append(f"{date} {role_icon} {result_icon} {slot['total_score']} балл.{pu_mark}")
        markup.add(types.InlineKeyboardButton(
            f"{date} {role_icon} {result_icon} игра #{game['id']}",
            callback_data=cb("game", "detail", game["id"]),
        ))
    if not items:
        lines.append("Игр пока нет.")

    nav = []
    if page > 1:
        nav.append(types.InlineKeyboardButton("◀️ Пред.", callback_data=cb("history", "list", page - 1)))
    if len(items) == data["per_page"]:
        nav.append(types.InlineKeyboardButton("▶️ След.", callback_data=cb("history", "list", page + 1)))
    if nav:
        markup.row(*nav)
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("profile", "open"))
