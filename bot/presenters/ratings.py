from typing import Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc


def build_ratings_message(data: dict, scope: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    lines = [f"🏆 <b>Общий рейтинг</b> — стр. {page}/{total_pages}", ""]
    for r in items:
        lines.append(f"{r['rank']}. {esc(r['display_name'])} — {r['win_rate']}% ({r['games_played']} игр)")
    if not items:
        lines.append("Пока пусто.")

    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("rating", "global"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))
