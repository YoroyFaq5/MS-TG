from typing import Optional, Tuple

from telebot import types


def build_ratings_message(data: dict, scope: str) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    items = data["items"]
    total_pages = data["total_pages"] or 1
    lines = [f"🏆 <b>Рейтинг</b> ({scope}) — стр. {data['page']}/{total_pages}", ""]
    for r in items:
        lines.append(f"{r['rank']}. {r['display_name']} — {r['win_rate']}% ({r['games_played']} игр)")
    if not items:
        lines.append("Пока пусто.")
    return "\n".join(lines), None
