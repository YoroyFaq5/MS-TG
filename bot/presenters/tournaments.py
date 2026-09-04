from typing import Optional, Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc, fmt_money, truncate

STATUS_ICONS = {"pending": "⏳", "active": "▶️", "finished": "🏁"}
STATUS_LABELS = {"pending": "Ожидают", "active": "Активные", "finished": "Завершённые"}
STATUS_FILTERS = [None, "active", "pending", "finished"]


def build_tournaments_list_message(
    data: dict, status: Optional[str] = None,
) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    label = STATUS_LABELS.get(status, "Все")
    lines = [f"🏟 <b>Турниры</b> — {label}, стр. {page}/{total_pages}", ""]
    for t in items:
        icon = STATUS_ICONS.get(t["status"], "")
        series_mark = " 🔗" if t.get("series_tournament_id") else ""
        lines.append(f"#{t['id']} {icon} {esc(t['name'])}{series_mark}")
    if not items:
        lines.append("Турниров пока нет.")

    markup = types.InlineKeyboardMarkup()
    filter_row = [
        types.InlineKeyboardButton(
            ("• " if status == s else "") + STATUS_LABELS.get(s, "Все"),
            callback_data=cb("tourn", "list", s or "-", 1),
        )
        for s in STATUS_FILTERS
    ]
    markup.row(*filter_row[:2])
    markup.row(*filter_row[2:])
    for t in items:
        icon = STATUS_ICONS.get(t["status"], "")
        series_mark = " 🔗" if t.get("series_tournament_id") else ""
        markup.add(types.InlineKeyboardButton(
            f"{icon} {truncate(t['name'], 40)}{series_mark}",
            callback_data=cb("tourn", "open", t["id"], t.get("series_tournament_id") or 0),
        ))
    if items:
        markup.row(*pagination_row(cb("tourn", "list", status or "-"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup)


def build_tournament_detail_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    t = data["tournament"]
    lines = [
        f"🏟 <b>{esc(t['name'])}</b> ({t['status']})",
        f"Тип: {t['type']} · Участников: {data['participant_count']}",
        f"Игр: {data['games_finished']}/{data['games_total']}",
    ]
    if data.get("active_stage"):
        lines.append(f"Текущий этап: {esc(data['active_stage']['name'])}")

    if not data.get("can_view_standings"):
        lines.append("\n🙈 Таблица очков и мест скрыта администратором.")
    else:
        ratings = data.get("player_ratings") or []
        if ratings:
            lines.append("")
            lines.append("Топ игроков:")
            for r in ratings[:10]:
                lines.append(f"{r['rank']}. {esc(r['display_name'])} — {r['win_rate']}%")

    tid = t["id"]
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎯 Fantasy", callback_data=cb("fantasy", "tourn", tid)),
    )
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("tourn", "list", "-", 1))


def build_series_tournament_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    st = data["series_tournament"]
    t = st["tournament"]
    lines = [
        f"🔗 <b>{esc(t['name'])}</b> — серийный турнир",
        f"Вечеров: {len(data['series'])}",
        "",
        "Общий рейтинг:",
    ]
    for e in data["overall_leaderboard"][:10]:
        lines.append(f"{e['rank']}. {esc(e['display_name'])} — {e['total_score']} ({e['series_played']} вечеров)")
    if not data["overall_leaderboard"]:
        lines.append("Пока нет результатов.")

    markup = types.InlineKeyboardMarkup()
    for s in sorted(data["series"], key=lambda s: s["order"]):
        status_icon = {"pending": "⏳", "active": "▶️", "finished": "🏁", "cancelled": "✖️"}.get(s["status"], "")
        markup.add(types.InlineKeyboardButton(
            f"{status_icon} {truncate(s['name'], 40)}",
            callback_data=cb("tourn", "series-evening", st["id"], s["id"]),
        ))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("tourn", "list", "-", 1))


def build_series_evening_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    st = data["series_tournament"]
    series = data["series"]
    lines = [
        f"🌆 <b>{esc(series['name'])}</b> — {esc(st['tournament']['name'])}",
        f"Игр: {series['games_count']} · Статус: {series['status']}",
        "",
        "Рейтинг вечера:",
    ]
    for r in data["leaderboard"][:15]:
        lines.append(f"{r['rank']}. {esc(r['display_name'])} — {r['total_score']} ({r['win_rate']}%)")
    if not data["leaderboard"]:
        lines.append("Пока нет результатов.")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(
        "🎯 Fantasy этого вечера",
        callback_data=cb("fantasy", "series", st["tournament_id"], series["id"]),
    ))
    return "\n".join(lines), add_nav_footer(
        markup, back_target=cb("tourn", "open", st["tournament_id"], st["id"]),
    )
