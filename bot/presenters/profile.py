from typing import Optional, Tuple

from telebot import types

from bot import i18n
from bot.config import Config
from bot.ui import esc


def build_not_linked_message() -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    text = (
        "🔗 Аккаунт ещё не привязан.\n\n"
        "Привяжи Telegram на сайте, чтобы получить доступ к профилю, "
        "статистике и уведомлениям."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔗 Привязать аккаунт", url=f"{Config.MAIN_API_BASE_URL.rstrip('/')}/profile/",
    ))
    return text, markup


def build_welcome_back_message(display_name: str) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    text = (
        f"👋 С возвращением, <b>{esc(display_name)}</b>!\n\n"
        "Пользуйся кнопками меню ниже — профиль, статистика, рейтинг и "
        "«🆚 Сравнить игроков»."
    )
    return text, None


def build_profile_card(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    player = data["player"]
    rank = data.get("global_rank")
    rank_text = f"#{rank}" if rank else "—"
    elo = round(data.get("elo", player["elo"]))
    games = i18n.fmt_count(data["total_games"], i18n.games_word)
    wins = i18n.fmt_count(data["total_wins"], i18n.wins_word)
    lines = [
        f"👤 <b>{esc(player['display_name'])}</b>",
        f"Эло: {elo} · Место в рейтинге: {rank_text}",
        f"{games} · {wins} ({i18n.fmt_percent(data['win_rate'])})",
        f"Баланс: {i18n.fmt_coins(data.get('coins', 0.0))}",
    ]
    equipped_title = data.get("equipped_title")
    if equipped_title:
        lines.append(f"🏅 {esc(equipped_title.get('name', ''))}")
    if data.get("bio"):
        lines.append(f"\n<i>{esc(data['bio'])}</i>")
    return "\n".join(lines), None
