from typing import Optional, Tuple

from telebot import types


def build_not_linked_message() -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    text = (
        "🔗 Аккаунт ещё не привязан.\n\n"
        "Зайдите на сайт → Профиль → «Войти через Telegram», чтобы привязать "
        "аккаунт и получить доступ к профилю, статистике и уведомлениям."
    )
    return text, None


def build_welcome_back_message(display_name: str) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    text = (
        f"👋 С возвращением, <b>{display_name}</b>!\n\n"
        "/me — профиль\n"
        "/stats — статистика\n"
        "/compare &lt;id игрока&gt; — сравнение"
    )
    return text, None


def build_profile_card(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    player = data["player"]
    rank = data.get("global_rank")
    rank_text = f"#{rank}" if rank else "—"
    lines = [
        f"👤 <b>{player['display_name']}</b>",
        f"ELO: {round(data.get('elo', player['elo']))} · Место в рейтинге: {rank_text}",
        f"Игр: {data['total_games']} · Побед: {data['total_wins']} ({data['win_rate']}%)",
        f"Монет: {round(data.get('coins', 0.0), 2)}",
    ]
    equipped_title = data.get("equipped_title")
    if equipped_title:
        lines.append(f"🏅 {equipped_title.get('name', '')}")
    if data.get("bio"):
        lines.append(f"\n<i>{data['bio']}</i>")
    return "\n".join(lines), None
