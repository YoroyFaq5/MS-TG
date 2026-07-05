from typing import Optional, Tuple

from telebot import types


def build_my_draft_message(draft: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    lines = [
        f"🎯 <b>Мой драфт</b> (турнир #{draft['tournament_id']})",
        f"Статус: {draft['status']} · Очки: {draft['total_points']}",
        "",
    ]
    if draft["picks"]:
        lines.append("Пики:")
        for p in draft["picks"]:
            lines.append(f"— {p['player_name']} ({p['points_earned']} очк.)")
    else:
        lines.append("Пока нет пиков.")
    return "\n".join(lines), None


def build_no_draft_message(tournament_id: int) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    text = (
        f"У вас ещё нет драфта для турнира #{tournament_id}.\n"
        f"Создать: <code>/fantasy_create {tournament_id}</code>"
    )
    return text, None


def build_available_message(players: list, tournament_id: int) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    lines = [f"Доступные игроки для пика (турнир #{tournament_id}):", ""]
    for p in players:
        lines.append(f"#{p['id']} {p['name']} (ELO {round(p['elo'])})")
    if not players:
        lines.append("Никого не осталось.")
    lines.append("")
    lines.append(f"Выбрать: <code>/fantasy_pick {tournament_id} &lt;id игрока&gt;</code>")
    return "\n".join(lines), None


def build_leaderboard_message(entries: list, tournament_id: int) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    lines = [f"🏆 <b>Fantasy — турнир #{tournament_id}</b>", ""]
    for e in entries:
        lines.append(f"{e['rank']}. {e['display_name']} — {e['total_points']} очк. ({e['pick_count']} пиков)")
    if not entries:
        lines.append("Пока пусто.")
    return "\n".join(lines), None
