"""
Presenters for the public group-chat commands (CLAUDE_TASK_BOT_RU_GROUPS.md,
раздел 3): /top, /season, /tournaments, /player, /compare, /game, /help.

Deliberately separate from the private inline-menu presenters even where
the underlying data is the same (season/tournament/game detail) — group
screens:
  - never paginate (one compact message, task п.3/7.5);
  - never use a callback_data button for "see more", only a URL/deep-link
    button into the bot's own private chat (task п.2.2/3) — a forwarded
    group message's button must not depend on a private_only=True
    callback handler that will just reject it;
  - never show personal/mutating actions.
"""
from typing import Optional, Tuple

from telebot import types

from bot import i18n
from bot.bot_identity import deep_link_url, bot_url
from bot.ui import esc


def _open_in_bot_button(payload: str, label: str = "🤖 Открыть в боте") -> types.InlineKeyboardButton:
    return types.InlineKeyboardButton(label, url=deep_link_url(payload))


def build_top_message(data: dict, limit: int) -> Tuple[str, types.InlineKeyboardMarkup]:
    items = data["items"][:limit]
    lines = [f"🏆 <b>Топ-{limit} рейтинга клуба</b>", ""]
    for r in items:
        games = i18n.fmt_count(r["games_played"], i18n.games_word)
        lines.append(f"{r['rank']}. {esc(r['display_name'])} — {i18n.fmt_percent(r['win_rate'])} ({games})")
    if not items:
        lines.append("Пока пусто.")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Открыть полный рейтинг", url=deep_link_url("rating")))
    return "\n".join(lines), markup


def build_group_season_message(season: Optional[dict], top5: list, min_games: int) -> Tuple[str, types.InlineKeyboardMarkup]:
    if not season:
        return "📅 Сейчас нет активного сезона.", types.InlineKeyboardMarkup()

    status = i18n.tr("season_status", season["status"])
    dates = f"{i18n.fmt_date_only(season['starts_at'])} — {i18n.fmt_date_only(season['ends_at'])}"
    lines = [
        f"📅 <b>{esc(season['name'])}</b> ({status})",
        dates,
        f"<i>Места 1–5 доступны игрокам с {i18n.fmt_count(min_games, i18n.games_word)}+ за сезон.</i>",
        "",
        "Топ-5:",
    ]
    for r in top5:
        floor_mark = "" if r["meets_top5_min_games"] else " 🔒"
        lines.append(f"{r['rank']}. {esc(r['display_name'])} — {i18n.fmt_score(r['season_rating'])}{floor_mark}")
    if not top5:
        lines.append("Пока нет сыгранных игр.")

    markup = types.InlineKeyboardMarkup()
    markup.add(_open_in_bot_button(f"season{season['id']}", "📊 Открыть таблицу сезона"))
    return "\n".join(lines), markup


def build_group_tournaments_message(tournaments: list) -> Tuple[str, types.InlineKeyboardMarkup]:
    lines = ["🏟 <b>Турниры клуба</b>", ""]
    markup = types.InlineKeyboardMarkup()
    for t in tournaments[:5]:
        status = i18n.tr("tournament_status", t["status"])
        date = i18n.fmt_date_only(t.get("started_at") or t.get("created_at"))
        lines.append(f"«{esc(t['name'])}» — {status} ({date})")
        markup.add(types.InlineKeyboardButton(
            f"🔗 {t['name'][:40]}", url=deep_link_url(f"t{t['id']}"),
        ))
    if not tournaments:
        lines.append("Сейчас нет активных или ожидаемых турниров.")
    return "\n".join(lines), markup


def build_group_player_card_message(player: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    rank_text = f"#{player['rank']}" if player.get("rank") else "—"
    games = i18n.fmt_count(player["games_played"], i18n.games_word)
    wins = i18n.fmt_count(player["games_won"], i18n.wins_word)
    lines = [
        f"👤 <b>{esc(player['display_name'])}</b>",
        f"Место: {rank_text} · Эло: {round(player['elo'])}",
        f"{games} · {wins} ({i18n.fmt_percent(player['win_rate'])})",
    ]
    markup = types.InlineKeyboardMarkup()
    return "\n".join(lines), markup


def build_player_disambiguation_message(candidates: list, query: str) -> Tuple[str, types.InlineKeyboardMarkup]:
    """Group-safe: buttons here don't carry personal state — tapping any
    of them just re-runs the same public /player lookup for that exact
    id, so an unrelated user tapping it produces the identical public
    result (no ownership check needed, see CLAUDE_TASK_BOT_RU_GROUPS.md
    п.2.2 — this is the case where no such check is required)."""
    from bot.keyboards.nav import cb

    lines = [f"Найдено несколько игроков по «{esc(query)}»:"]
    markup = types.InlineKeyboardMarkup()
    for p in candidates[:5]:
        markup.add(types.InlineKeyboardButton(
            f"{p['display_name']} (Эло {round(p['elo'])})", callback_data=cb("gplayer", "show", p["id"]),
        ))
    return "\n".join(lines), markup


def build_player_not_found_message(query: str) -> str:
    return f"Игрок «{esc(query)}» не найден. Проверь ник и попробуй снова."


def build_group_compare_message(data: dict, resolved_note: str = "") -> Tuple[str, types.InlineKeyboardMarkup]:
    from bot.presenters.vs import build_vs_message
    text, _ = build_vs_message(data)
    if resolved_note:
        text = f"{resolved_note}\n\n{text}"
    return text, types.InlineKeyboardMarkup()


def build_group_game_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    from bot.presenters.games import ROLE_ICONS, WIN_SIDE_ICONS

    game = data["game"]
    win_side_label = f"{WIN_SIDE_ICONS.get(game['win_side'], '')} {i18n.tr('win_side', game['win_side'])}"
    lines = [
        f"🎮 <b>Игра #{game['id']}</b>",
        f"{i18n.fmt_datetime(game['played_at'])} · Победа: {win_side_label}",
        "",
    ]
    for s in data["slots"]:
        icon = ROLE_ICONS.get(s["role"], "")
        name = esc(s["player_name"] or f"#{s['player_id']}")
        lines.append(f"{s['seat_number']}. {icon} {name} — {i18n.fmt_points(s['total_score'])}")

    markup = types.InlineKeyboardMarkup()
    markup.add(_open_in_bot_button(f"g{game['id']}", "🎮 Открыть в боте"))
    return "\n".join(lines), markup


def build_group_help_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = (
        "🤖 <b>Команды общего чата</b>\n\n"
        "/top [3-10] — топ рейтинга клуба\n"
        "/season — текущий сезон\n"
        "/tournaments — активные и ближайшие турниры\n"
        "/player &lt;ник&gt; — карточка игрока\n"
        "/compare &lt;ник 1&gt; | &lt;ник 2&gt; — сравнение игроков\n"
        "/game &lt;номер&gt; — карточка завершённой игры\n"
        "/help — эта справка\n\n"
        "Личный кабинет, покупки, подарки и Фэнтези — только в личном чате с ботом."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🤖 Открыть личный кабинет", url=bot_url()))
    return text, markup


def build_group_start_message() -> Tuple[str, types.InlineKeyboardMarkup]:
    text = (
        "👋 Привет! В этом чате доступны публичные команды:\n\n"
        "/top, /season, /tournaments, /player, /compare, /game, /help\n\n"
        "Личный кабинет — в личном чате с ботом."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🤖 Открыть личный кабинет", url=bot_url()))
    return text, markup


def build_rate_limited_message() -> str:
    return "⏳ Слишком много команд подряд — подожди немного."


def build_usage_error_message(usage: str) -> str:
    return f"Использование: <code>{usage}</code>"
