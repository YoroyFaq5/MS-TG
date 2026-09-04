from typing import Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc

ROLE_ICONS = {"civilian": "👤", "mafia": "🔫", "don": "🎩", "sheriff": "🔍"}
ROLE_LABELS = {"civilian": "Мирный", "mafia": "Мафия", "don": "Дон", "sheriff": "Шериф"}


def build_game_detail_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    game = data["game"]
    win_side_label = {"mafia": "🔫 Мафия", "city": "🏙 Город", "none": "Ничья"}.get(game["win_side"], "—")
    lines = [
        f"🎮 <b>Игра #{game['id']}</b>",
        f"{game['played_at'][:16].replace('T', ' ')} · Победа: {win_side_label}",
        "",
    ]
    for s in data["slots"]:
        icon = ROLE_ICONS.get(s["role"], "")
        pu_mark = " 🎯" if s["is_pu"] else ""
        name = esc(s["player_name"] or f"#{s['player_id']}")
        lines.append(f"{s['seat_number']}. {icon} {name} — {s['total_score']} балл.{pu_mark}")

    markup = types.InlineKeyboardMarkup()
    if data.get("tournament_series_id") and data.get("series_id"):
        markup.row(types.InlineKeyboardButton(
            "🌆 Вечер серии",
            callback_data=cb("tourn", "series-evening", data["tournament_series_id"], data["series_id"]),
        ))
    elif data.get("tournament_id"):
        markup.row(types.InlineKeyboardButton(
            "🏟 Турнир", callback_data=cb("tourn", "open", data["tournament_id"], 0),
        ))
    return "\n".join(lines), add_nav_footer(markup)
