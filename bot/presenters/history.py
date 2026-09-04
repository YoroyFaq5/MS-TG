from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import truncate

ROLE_ICONS = {"civilian": "👤", "mafia": "🔫", "don": "🎩", "sheriff": "🔍"}


def build_history_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data.get("total_pages") or 1
    lines = [f"📜 <b>История игр</b> — {i18n.page_indicator(page, total_pages)}", ""]
    markup = types.InlineKeyboardMarkup()
    for item in items:
        slot, game = item["slot"], item["game"]
        date = i18n.fmt_date_only(game["played_at"])
        result_icon = "✅" if item["won"] else "❌"
        role_icon = ROLE_ICONS.get(slot["role"], "")
        pu_mark = " 🎯" if slot["is_pu"] else ""
        lines.append(f"{date} {role_icon} {result_icon} {i18n.fmt_points(slot['total_score'])}{pu_mark}")
        markup.add(types.InlineKeyboardButton(
            f"{date} {role_icon} {result_icon} игра #{game['id']}",
            callback_data=cb("game", "detail", game["id"]),
        ))
    if not items:
        lines.append("Игр пока нет.")

    # has_next приходит с сервера (Bot API теперь возвращает total_pages/
    # has_next наравне с has_next для истории игр — см.
    # CLAUDE_TASK_BOT_RU_GROUPS.md п.5.5); старый heuristic по размеру
    # страницы оставлен только как fallback для не обновлённого API.
    has_next = data.get("has_next")
    if has_next is None:
        has_next = len(items) == data.get("per_page")

    nav = []
    if page > 1:
        nav.append(types.InlineKeyboardButton("◀️ Пред.", callback_data=cb("history", "list", page - 1)))
    if has_next:
        nav.append(types.InlineKeyboardButton("▶️ След.", callback_data=cb("history", "list", page + 1)))
    if nav:
        markup.row(*nav)
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("profile", "open"))
