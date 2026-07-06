from typing import Optional, Tuple

from telebot import types

STATUS_ICONS = {"pending": "⏳", "active": "▶️", "finished": "🏁"}


def build_tournaments_list_message(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    items = data["items"]
    lines = ["🏟 <b>Турниры</b>", ""]
    for t in items:
        icon = STATUS_ICONS.get(t["status"], "")
        lines.append(f"#{t['id']} {icon} {t['name']} ({t['status']})")
    if not items:
        lines.append("Турниров пока нет.")

    markup = None
    if items:
        markup = types.InlineKeyboardMarkup()
        for t in items:
            icon = STATUS_ICONS.get(t["status"], "")
            markup.add(types.InlineKeyboardButton(
                f"{icon} {t['name']}", callback_data=f"tourn:{t['id']}",
            ))
    return "\n".join(lines), markup


def build_tournament_detail_message(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    t = data["tournament"]
    lines = [
        f"🏟 <b>{t['name']}</b> ({t['status']})",
        f"Тип: {t['type']} · Участников: {data['participant_count']}",
        f"Игр: {data['games_finished']}/{data['games_total']}",
    ]
    if data.get("active_stage"):
        lines.append(f"Текущий этап: {data['active_stage']['name']}")

    ratings = data.get("player_ratings") or []
    if ratings:
        lines.append("")
        lines.append("Топ игроков:")
        for r in ratings[:10]:
            lines.append(f"{r['rank']}. {r['display_name']} — {r['win_rate']}%")
    return "\n".join(lines), None
