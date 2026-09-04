from typing import Optional, Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb, pagination_row
from bot.ui import esc


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
        status = i18n.tr("season_status", season["status"])
        text = (
            f"📅 <b>{esc(season['name'])}</b>\n"
            f"Статус: {status} · Вес GG: {season['gg_weight']}\n"
        )
        if season.get("winner_name"):
            text += f"Победитель: {esc(season['winner_name'])} ({i18n.fmt_points(season['winner_score'])})\n"
    markup = types.InlineKeyboardMarkup()
    if season:
        markup.row(types.InlineKeyboardButton(
            "📊 Таблица сезона", callback_data=cb("season", "detail", season["id"], 1),
        ))
        markup.row(types.InlineKeyboardButton(
            "📍 Моё место", callback_data=cb("season", "myplace", season["id"]),
        ))
        markup.row(types.InlineKeyboardButton("🔄 Обновить", callback_data=cb("season", "current")))
    return text, add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_seasons_list_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    year = data["year"]
    seasons = data["seasons"]
    text = f"🗓 <b>Сезоны {year} года</b>"
    markup = types.InlineKeyboardMarkup()
    status_icons = {"active": "▶️", "finished": "🏁", "waiting_tiebreak": "⚖️"}
    for s in seasons:
        icon = status_icons.get(s["status"], "")
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
        f"📊 <b>{esc(season['name'])}</b> — {i18n.page_indicator(page, total_pages)}",
        f"<i>Места 1–5 доступны игрокам с {i18n.fmt_count(min_games, i18n.games_word)}+ за сезон.</i>",
        "",
    ]
    for r in items:
        floor_mark = "" if r["meets_top5_min_games"] else " 🔒"
        games = i18n.fmt_count(r["games_played"], i18n.games_word)
        lines.append(
            f"{r['rank']}. {esc(r['display_name'])} — {i18n.fmt_score(r['season_rating'])} ({games}{floor_mark})"
        )
    if not items:
        lines.append("В этом сезоне ещё нет игр.")

    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("season", "detail", season["id"]), page, total_pages))
    markup.row(types.InlineKeyboardButton(
        "🔄 Обновить", callback_data=cb("season", "detail", season["id"], page),
    ))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_my_place_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    season = data["season"]
    entry = data.get("entry")
    min_games = data["min_games_for_top5"]

    lines = [f"📍 <b>Моё место — {esc(season['name'])}</b>", ""]
    if not entry:
        lines.append("Пока нет сыгранных рейтинговых игр в этом сезоне.")
    else:
        games = i18n.fmt_count(entry["games_played"], i18n.games_word)
        wins = i18n.fmt_count(entry["games_won"], i18n.wins_word)
        lines.append(f"Место: <b>{entry['rank']}</b> · Очки: {i18n.fmt_score(entry['season_rating'])}")
        lines.append(f"{games} · {wins} ({i18n.fmt_percent(entry['win_rate_pct'])})")
        lines.append(f"GG: {i18n.fmt_score(entry['gg_total'])} (вес {entry['gg_weight']})")
        if not entry["meets_top5_min_games"]:
            need = i18n.fmt_count(entry["games_needed_for_top5"], i18n.games_word)
            lines.append(
                f"🔒 Ещё {need} до допуска на места 1–5 "
                f"(нужно минимум {i18n.fmt_count(min_games, i18n.games_word)})."
            )
        above = data.get("neighbor_above")
        below = data.get("neighbor_below")
        if above:
            lines.append(f"\n⬆️ Выше: {esc(above['display_name'])} — {i18n.fmt_score(above['season_rating'])}")
        if below:
            lines.append(f"⬇️ Ниже: {esc(below['display_name'])} — {i18n.fmt_score(below['season_rating'])}")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(
        "🔄 Обновить", callback_data=cb("season", "myplace", season["id"]),
    ))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))


def build_season_winners_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    lines = [f"🏅 <b>История победителей</b> — {i18n.page_indicator(page, total_pages)}", ""]
    for s in items:
        lines.append(f"{s['year']} · Сезон {s['number']}: {esc(s['winner_name'])} ({i18n.fmt_points(s['winner_score'])})")
    if not items:
        lines.append("Победителей пока нет.")

    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("season", "winners"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("rating", "hub"))
