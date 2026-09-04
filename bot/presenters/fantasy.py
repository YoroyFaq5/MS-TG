"""
Fantasy screens. Every scope-carrying callback encodes exactly
(tournament_id, series_id_or_0, is_practice_0_or_1) as three trailing
ints — the bot never needs its own copy of "which draft is this", it just
re-resolves the caller's draft (if any) for that scope via
GET /fantasy/my on each action. This keeps callback_data short and avoids
a second source of truth for draft_id vs scope.
"""
from typing import Optional, Tuple

from telebot import types

from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc, truncate


def scope_cb(action: str, tournament_id: int, series_id: int = 0, is_practice: bool = False) -> str:
    return cb("fantasy", action, tournament_id, series_id, int(is_practice))


def build_fantasy_events_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🎯 <b>Fantasy</b>\n\nВыбери турнир или вечер серии для драфта:"
    markup = types.InlineKeyboardMarkup()

    for item in data.get("tournaments", []):
        t = item["tournament"]
        mark = "✅" if item.get("my_draft_id") else "➕"
        markup.add(types.InlineKeyboardButton(
            f"{mark} {truncate(t['name'], 40)}", callback_data=scope_cb("open", t["id"]),
        ))
    for item in data.get("series", []):
        s = item["series"]
        mark = "✅" if item.get("my_draft_id") else "➕"
        markup.add(types.InlineKeyboardButton(
            f"{mark} 🌆 {truncate(s['name'], 36)}",
            callback_data=scope_cb("open", item["tournament_id"], s["id"]),
        ))
    if not data.get("tournaments") and not data.get("series"):
        text += "\n\nСейчас нет доступных для драфта событий."

    markup.row(types.InlineKeyboardButton("📜 Мои драфты (история)", callback_data=cb("fantasy", "history", 1)))
    return text, add_nav_footer(markup)


def _scope_header(tournament_id: int, series_id: int, is_practice: bool, name: str) -> str:
    kind = "🌆 вечер" if series_id else "🏟 турнир"
    mode = " · 🎓 тренировочный" if is_practice else ""
    return f"🎯 <b>Fantasy — {kind} «{esc(name)}»</b>{mode}"


def build_fantasy_hub_message(
    tournament_id: int, series_id: int, is_practice: bool, name: str, draft: Optional[dict],
) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [_scope_header(tournament_id, series_id, is_practice, name), ""]
    if draft:
        lines.append(f"Статус: {draft['status']} · Пиков: {draft['pick_count']} · Очки: {draft['total_points']}")
    else:
        lines.append("У вас ещё нет драфта здесь.")

    markup = types.InlineKeyboardMarkup()
    if draft:
        markup.row(types.InlineKeyboardButton(
            "🎯 Мой драфт", callback_data=scope_cb("my", tournament_id, series_id, is_practice),
        ))
    else:
        markup.row(types.InlineKeyboardButton(
            "➕ Создать драфт", callback_data=scope_cb("create", tournament_id, series_id, is_practice),
        ))
    markup.row(types.InlineKeyboardButton(
        "🏆 Лидеры", callback_data=scope_cb("lb", tournament_id, series_id, is_practice),
    ))
    if not is_practice:
        markup.row(types.InlineKeyboardButton(
            "🎓 Тренировочный режим", callback_data=scope_cb("open", tournament_id, series_id, True),
        ))
    else:
        markup.row(types.InlineKeyboardButton(
            "💰 Обычный (платный) режим", callback_data=scope_cb("open", tournament_id, series_id, False),
        ))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("fantasy", "events"))


def build_my_draft_message(
    draft: dict, tournament_id: int, series_id: int, is_practice: bool,
) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [
        f"🎯 <b>Мой драфт</b>", f"Статус: {draft['status']} · Очки: {draft['total_points']}", "",
    ]
    markup = types.InlineKeyboardMarkup()
    if draft["picks"]:
        lines.append("Пики:")
        for p in draft["picks"]:
            lines.append(f"— {esc(p['player_name'])} ({p['points_earned']} очк.)")
            if draft["status"] == "open":
                markup.add(types.InlineKeyboardButton(
                    f"❌ {truncate(p['player_name'], 30)}",
                    callback_data=cb("fantasy", "unpick", draft["id"], p["player_id"]),
                ))
    else:
        lines.append("Пока нет пиков.")

    if draft["status"] == "open":
        markup.row(types.InlineKeyboardButton(
            "➕ Добавить пик", callback_data=scope_cb("avail", tournament_id, series_id, is_practice),
        ))
        markup.row(types.InlineKeyboardButton(
            "🗑 Отменить драфт (вернуть монеты)",
            callback_data=scope_cb("cancel-confirm", tournament_id, series_id, is_practice),
        ))
    return "\n".join(lines), add_nav_footer(
        markup, back_target=scope_cb("open", tournament_id, series_id, is_practice),
    )


def build_cancel_confirm_message(
    tournament_id: int, series_id: int, is_practice: bool,
) -> Tuple[str, types.InlineKeyboardMarkup]:
    text = "🗑 Точно отменить драфт? Уже сделанные пики будут потеряны, оплата вернётся на баланс."
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(
            "✅ Да, отменить", callback_data=scope_cb("cancel", tournament_id, series_id, is_practice),
        ),
        types.InlineKeyboardButton(
            "✖️ Нет", callback_data=scope_cb("my", tournament_id, series_id, is_practice),
        ),
    )
    return text, markup


def build_available_message(
    players: list, tournament_id: int, series_id: int, is_practice: bool,
) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = ["Доступные игроки для пика:", ""]
    markup = types.InlineKeyboardMarkup()
    for p in players:
        lines.append(f"{esc(p['name'])} (ELO {round(p['elo'])})")
        markup.add(types.InlineKeyboardButton(
            f"{truncate(p['name'], 30)} (ELO {round(p['elo'])})",
            callback_data=cb("fantasy", "pickf", tournament_id, series_id, int(is_practice), p["id"]),
        ))
    if not players:
        lines.append("Никого не осталось.")
    return "\n".join(lines), add_nav_footer(
        markup, back_target=scope_cb("my", tournament_id, series_id, is_practice),
    )


def build_leaderboard_message(
    entries: list, name: str, tournament_id: int, series_id: int, is_practice: bool,
) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = [f"🏆 <b>Fantasy — {esc(name)}</b>", ""]
    for e in entries:
        lines.append(f"{e['rank']}. {esc(e['display_name'])} — {e['total_points']} очк. ({e['pick_count']} пиков)")
    if not entries:
        lines.append("Пока пусто.")
    return "\n".join(lines), add_nav_footer(
        types.InlineKeyboardMarkup(), back_target=scope_cb("open", tournament_id, series_id, is_practice),
    )


def build_history_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"]
    page = data["page"]
    total_pages = data["total_pages"] or 1
    lines = [f"📜 <b>Мои Fantasy-драфты</b> — стр. {page}/{total_pages}", ""]
    for d in items:
        scope = "🌆 вечер" if d.get("tournament_series_id") else "🏟 турнир"
        mode = " 🎓" if d["is_practice"] else ""
        lines.append(f"{scope}{mode} · {d['status']} · {d['total_points']} очк. ({d['pick_count']} пиков)")
    if not items:
        lines.append("Драфтов пока нет.")

    from bot.keyboards.nav import pagination_row
    markup = types.InlineKeyboardMarkup()
    if items:
        markup.row(*pagination_row(cb("fantasy", "history"), page, total_pages))
    return "\n".join(lines), add_nav_footer(markup, back_target=cb("fantasy", "events"))
