from typing import Tuple

from telebot import types

from bot import i18n
from bot.keyboards.nav import add_nav_footer, cb
from bot.ui import esc


def build_stats_message(data: dict) -> Tuple[str, types.InlineKeyboardMarkup]:
    s = data["stats"]
    games = i18n.fmt_count(s["total_games"], i18n.games_word)
    wins = i18n.fmt_count(s["total_wins"], i18n.wins_word)
    lines = [
        f"📊 <b>Статистика — {esc(s['display_name'])}</b>",
        "",
        f"{games} · {wins} ({i18n.fmt_percent(s['win_rate'])})",
        f"Ср. баллы: {i18n.fmt_score(s['avg_score'])} · "
        f"Лучший: {i18n.fmt_score(s['best_score'])} · Худший: {i18n.fmt_score(s['worst_score'])}",
        f"Текущая серия: {s['current_streak_signed']} "
        f"(лучшая победная — {s['longest_streak']}, худшая проигрышная — {s['longest_loss_streak']})",
        f"Раз был ПУ: {s['pu_count']} (в т.ч. Шерифом: {s['pu_sheriff_count']})",
    ]
    if s.get("pu_accuracy") is not None:
        lines.append(f"Точность ЛХ: {i18n.fmt_percent(s['pu_accuracy'])}")
    if s.get("best_day_wins"):
        bd = s["best_day_wins"]
        lines.append(f"Лучший день по победам: {i18n.fmt_date_only(bd['date'])} — {bd['wins']} из {bd['games']}")
    if s.get("best_day_bonus"):
        bb = s["best_day_bonus"]
        lines.append(f"Лучший день по бонусам: {i18n.fmt_date_only(bb['date'])} — +{i18n.fmt_score(bb['bonus'])}")

    cmp = data.get("comparison_stats")
    if cmp:
        lines.append("")
        lines.append(
            f"📈 Место в клубе: #{cmp['rank']} из {cmp['total_ranked_players']}\n"
            f"Эло {round(cmp['elo'])} (клуб {round(cmp['club_avg_elo'])}, лучше {i18n.fmt_percent(cmp['elo_percentile'])})\n"
            f"Процент побед {i18n.fmt_percent(cmp['win_rate'])} (клуб {i18n.fmt_percent(cmp['club_avg_win_rate'])}, "
            f"лучше {i18n.fmt_percent(cmp['win_rate_percentile'])})"
        )
    return "\n".join(lines), add_nav_footer(types.InlineKeyboardMarkup(), back_target=cb("profile", "open"))
