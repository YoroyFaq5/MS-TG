from typing import Optional, Tuple

from telebot import types


def build_compare_message(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    a, b = data["player_a"], data["player_b"]
    sa, sb = data["stats_a"], data["stats_b"]
    lines = [
        f"⚖️ <b>{a['display_name']}</b> vs <b>{b['display_name']}</b>",
        "",
        f"ELO: {sa['elo']} vs {sb['elo']}",
        f"Винрейт: {sa['win_rate']}% vs {sb['win_rate']}%",
        f"Ср. баллы: {sa['avg_score']} vs {sb['avg_score']}",
        f"Игр: {sa['total_games']} vs {sb['total_games']}",
    ]
    h2h = data.get("head_to_head")
    if h2h:
        lines.append("")
        lines.append(
            f"⚔️ Личные встречи: {h2h['wins']}-{h2h['draws']}-{h2h['losses']} "
            f"(побед {a['display_name']} — одна команда/ничья — побед {b['display_name']})"
        )
    return "\n".join(lines), None
