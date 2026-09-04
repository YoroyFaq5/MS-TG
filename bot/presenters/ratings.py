from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc


def build_ratings_message(data: dict, scope: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    lines = [f"🏆 <b>Общий рейтинг</b> — {i18n.page_indicator(page, total_pages)}", ""]
    for r in items:
        games = i18n.fmt_count(r["games_played"], i18n.games_word)
        lines.append(f"{r['rank']}. {esc(r['display_name'])} — {i18n.fmt_percent(r['win_rate'])} ({games})")
    if not items:
        lines.append("Пока пусто.")

    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("rating", "global"), page, total_pages))
    markup.row(types.InlineKeyboardButton("🔄 Обновить", callback_data=cb("rating", "global", page)))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))
