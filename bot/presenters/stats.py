from typing import Optional, Tuple

from telebot import types


def build_stats_message(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    s = data["stats"]
    lines = [
        f"📊 <b>Статистика — {s['display_name']}</b>",
        "",
        f"Игр: {s['total_games']} · Побед: {s['total_wins']} ({s['win_rate']}%)",
        f"Ср. баллы: {s['avg_score']} · Лучший: {s['best_score']} · Худший: {s['worst_score']}",
        f"Текущая серия: {s['current_streak_signed']} "
        f"(лучшая победная — {s['longest_streak']}, худшая проигрышная — {s['longest_loss_streak']})",
        f"Раз был ПУ: {s['pu_count']} (в т.ч. Шерифом: {s['pu_sheriff_count']})",
    ]
    if s.get("pu_accuracy") is not None:
        lines.append(f"Точность ЛХ: {s['pu_accuracy']}%")
    if s.get("best_day_wins"):
        bd = s["best_day_wins"]
        lines.append(f"Лучший день по победам: {bd['date']} — {bd['wins']} из {bd['games']}")
    if s.get("best_day_bonus"):
        bb = s["best_day_bonus"]
        lines.append(f"Лучший день по бонусам: {bb['date']} — +{bb['bonus']}")

    cmp = data.get("comparison_stats")
    if cmp:
        lines.append("")
        lines.append(
            f"📈 Место в клубе: #{cmp['rank']} из {cmp['total_ranked_players']}\n"
            f"ELO {cmp['elo']} (клуб {cmp['club_avg_elo']}, лучше {cmp['elo_percentile']}%)\n"
            f"Винрейт {cmp['win_rate']}% (клуб {cmp['club_avg_win_rate']}%, "
            f"лучше {cmp['win_rate_percentile']}%)"
        )
    return "\n".join(lines), None
