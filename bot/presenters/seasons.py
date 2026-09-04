from typing import Optional, Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc, fmt_money


def build_ratings_hub_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🏆 <b>Рейтинги</b>\n\nВыбери, что посмотреть:"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🌐 Общий рейтинг", callback_data=cb("rating", "global", 1)))
    markup.row(types.InlineKeyboardButton("📅 Текущий сезон", callback_data=cb("season", "current")))
    markup.row(types.InlineKeyboardButton("🗓 Сезоны года", callback_data=cb("season", "list")))
    markup.row(types.InlineKeyboardButton("📍 Моё место (сезон)", callback_data=cb("season", "myplace-current")))
    markup.row(types.InlineKeyboardButton("🏅 История победителей", callback_data=cb("season", "winners", 1)))
    return text, add_nav_footer(markup, include_home=True)


def build_season_summary_message(season: Optional[dict]) -> Tuple[str, types.InlineKeyboardMarkup]:
    if not season:
        text = "Сейчас нет активного сезона."
    else:
        text = (
            f"📅 <b>{esc(season['name'])}</b>\n"
            f"Статус: {season['status']} · Вес GG: {season['gg_weight']}\n"
        )
        if season.get("winner_name"):
            text += f"Победитель: {esc(season['winner_name'])} ({season['winner_score']} очков)\n"
    markup = types.InlineKeyboardMarkup()
    if season:
        markup.row(types.InlineKeyboardButton(
            "📊 Таблица сезона", callback_data=cb("season", "detail", season["id"], 1),
        ))
        markup.row(types.InlineKeyboardButton(
            "📍 Моё место", callback_data=cb("season", "myplace", season["id"]),
        ))
    return text, add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_seasons_list_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    year = data["year"]
    seasons = data["seasons"]
    text = f"🗓 <b>Сезоны {year} года</b>"
    markup = types.InlineKeyboardMarkup()
    for s in seasons:
        icon = {"active": "▶️", "finished": "🏁", "waiting_tiebreak": "⚖️"}.get(s["status"], "")
        markup.add(types.InlineKeyboardButton(
            f"{icon} {s['name']}", callback_data=cb("season", "detail", s["id"], 1),
        ))
    return text, add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_season_detail_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    season = data["season"]
    pagination = data["ratings"]
    items = pagination["items"]
    page = pagination["page"]
    total_pages = pagination["total_pages"] or 1
    min_games = data["min_games_for_top5"]

    lines = [
        f"📊 <b>{esc(season['name'])}</b> — стр. {page}/{total_pages}",
        f"<i>Места 1–5 доступны игрокам с {min_games}+ играми за сезон.</i>",
        "",
    ]
    for r in items:
        floor_mark = "" if r["meets_top5_min_games"] else " 🔒"
        lines.append(
            f"{r['rank']}. {esc(r['display_name'])} — {r['season_rating']} "
            f"({r['games_played']} игр{floor_mark})"
        )
    if not items:
        lines.append("В этом сезоне ещё нет игр.")

    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("season", "detail", season["id"]), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_my_place_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    season = data["season"]
    entry = data.get("entry")
    min_games = data["min_games_for_top5"]

    lines = [f"📍 <b>Моё место — {esc(season['name'])}</b>", ""]
    if not entry:
        lines.append("Вы ещё не сыграли рейтинговых игр в этом сезоне.")
    else:
        lines.append(f"Место: <b>{entry['rank']}</b> · Очки: {entry['season_rating']}")
        lines.append(f"Игр: {entry['games_played']} · Побед: {entry['games_won']} ({entry['win_rate_pct']}%)")
        lines.append(f"GG: {entry['gg_total']} (вес {entry['gg_weight']})")
        if not entry["meets_top5_min_games"]:
            lines.append(
                f"🔒 Ещё {entry['games_needed_for_top5']} игр(ы) до допуска на места 1–5 "
                f"(нужно минимум {min_games})."
            )
        above = data.get("neighbor_above")
        below = data.get("neighbor_below")
        if above:
            lines.append(f"\n⬆️ Выше: {esc(above['display_name'])} — {above['season_rating']}")
        if below:
            lines.append(f"⬇️ Ниже: {esc(below['display_name'])} — {below['season_rating']}")

    markup = types.InlineKeyboardMarkup()
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_season_winners_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    lines = [f"🏅 <b>История победителей</b> — стр. {page}/{total_pages}", ""]
    for s in items:
        lines.append(f"{s['year']} · Сезон {s['number']}: {esc(s['winner_name'])} ({s['winner_score']} очк.)")
    if not items:
        lines.append("Победителей пока нет.")

    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("season", "winners"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))
