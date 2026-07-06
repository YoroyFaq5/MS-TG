from typing import Optional, Tuple

from telebot import types


def build_ratings_message(data: dict, scope: str) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    lines = [f"🏆 <b>Рейтинг</b> ({scope}) — стр. {page}/{total_pages}", ""]
    for r in items:
        lines.append(f"{r['rank']}. {r['display_name']} — {r['win_rate']}% ({r['games_played']} игр)")
    if not items:
        lines.append("Пока пусто.")

    markup = None
    nav = []
    if page > 1:
        nav.append(types.InlineKeyboardButton("◀️ Пред.", callback_data=f"rating:{page - 1}"))
    if page < total_pages:
        nav.append(types.InlineKeyboardButton("▶️ След.", callback_data=f"rating:{page + 1}"))
    if nav:
        markup = types.InlineKeyboardMarkup()
        markup.row(*nav)
    return "\n".join(lines), markup
