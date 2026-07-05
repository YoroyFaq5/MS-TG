from typing import Optional, Tuple

from telebot import types

ROLE_ICONS = {"civilian": "👤", "mafia": "🔫", "don": "🎩", "sheriff": "🔍"}


def build_history_message(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    items = data["items"]
    lines = [f"📜 <b>История игр</b> — стр. {data['page']}", ""]
    for item in items:
        slot, game = item["slot"], item["game"]
        date = game["played_at"][:10]
        result_icon = "✅" if item["won"] else "❌"
        role_icon = ROLE_ICONS.get(slot["role"], "")
        pu_mark = " 🎯" if slot["is_pu"] else ""
        lines.append(f"{date} {role_icon} {result_icon} {slot['total_score']} балл.{pu_mark}")
    if not items:
        lines.append("Игр пока нет.")
    return "\n".join(lines), None
