"""
"👤 Мой кабинет" hub screen — bundles profile/stats/history/achievements/
titles/account behind one short entry screen (see PROMPT_FOR_CLAUDE_BOT.md
section 2, item 1) instead of the old flat set of Reply Keyboard buttons.
"""
from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc


def build_profile_hub_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    player = data["player"]
    rank = data.get("global_rank")
    rank_text = f"#{rank}" if rank else "—"
    games = i18n.fmt_count(data["total_games"], i18n.games_word)
    wins = i18n.fmt_count(data["total_wins"], i18n.wins_word)
    lines = [
        f"👤 <b>{esc(player['display_name'])}</b>",
        f"Эло: {round(data.get('elo', player['elo']))} · Место: {rank_text}",
        f"{games} · {wins} ({i18n.fmt_percent(data['win_rate'])})",
        f"Баланс: {i18n.fmt_coins(data.get('coins', 0.0))}",
    ]
    equipped_title = data.get("equipped_title")
    if equipped_title:
        lines.append(f"🏅 {esc(equipped_title.get('name', ''))}")

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📊 Статистика", callback_data=cb("profile", "stats")),
        types.InlineKeyboardButton("📜 История игр", callback_data=cb("history", "list", 1)),
    )
    markup.row(
        types.InlineKeyboardButton("🏅 Достижения", callback_data=cb("profile", "achievements")),
        types.InlineKeyboardButton("🎖 Титулы", callback_data=cb("ach", "titles")),
    )
    markup.row(
        types.InlineKeyboardButton("💰 Баланс", callback_data=cb("profile", "balance")),
        types.InlineKeyboardButton("⚙️ Аккаунт", callback_data=cb("profile", "account")),
    )
    return "\n".join(lines), add_nav_footer(markup)
