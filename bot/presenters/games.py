from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc

ROLE_ICONS = {"civilian": "👤", "mafia": "🔫", "don": "🎩", "sheriff": "🔍"}
WIN_SIDE_ICONS = {"mafia": "🔫", "city": "🏙", "none": "🤝"}


def build_game_detail_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    game = data["game"]
    win_side_label = f"{WIN_SIDE_ICONS.get(game['win_side'], '')} {i18n.tr('win_side', game['win_side'])}"
    lines = [
        f"🎮 <b>Игра #{game['id']}</b>",
        f"{i18n.fmt_datetime(game['played_at'])} · Победа: {win_side_label}",
        "",
    ]
    for s in data["slots"]:
        icon = ROLE_ICONS.get(s["role"], "")
        role_label = i18n.tr("role", s["role"])
        pu_mark = " 🎯" if s["is_pu"] else ""
        name = esc(s["player_name"] or f"#{s['player_id']}")
        score = i18n.fmt_points(s["total_score"])
        lines.append(f"{s['seat_number']}. {icon} {name} — {role_label}, {score}{pu_mark}")

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
