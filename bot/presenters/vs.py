import random
from typing import List, Optional, Tuple

from telebot import types

_LANDSLIDE = [
    "{winner} раскатал(а) {loser} по асфальту клуба 🚂💥",
    "{winner} сегодня в форме бога — {loser} даже не понял(а), что произошло 🔥",
    "Разгром! {winner} забрал(а) практически всё 👑",
]
_CLOSE = [
    "На волоске! {winner} выцарапал(а) победу у самого края 😅",
    "Почти на равных, но {winner} чуть хитрее 🎯",
    "Соседи по силе — но перевес у {winner} 🤏",
]
_TIE = [
    "Ничья! Оба заслуживают короны 🤝👑",
    "Статы 1-в-1 — решать придётся словом на арене, а не цифрами 🎭",
    "Идеальный баланс сил ⚖️",
]

# (иконка+название, ключ в stats_a/stats_b, формат значения)
_STATS = [
    ("⚔️ Атака", "avg_score", "{:.2f}"),
    ("🛡️ Защита", "win_rate", "{:.0f}%"),
    ("❤️ Живучесть", "total_games", "{}"),
    ("⚡ Скорость", "elo", "{:.0f}"),
    ("🎯 Меткость", "pu_accuracy", "{:.0f}%"),
]


def _stat_line(label: str, val_a, val_b, fmt: str) -> Tuple[str, int, int]:
    a_str, b_str = fmt.format(val_a), fmt.format(val_b)
    if val_a > val_b:
        return f"{label}: {a_str} 🏆 vs {b_str}", 1, 0
    if val_b > val_a:
        return f"{label}: {a_str} vs {b_str} 🏆", 0, 1
    return f"{label}: {a_str} vs {b_str}", 0, 0


def build_vs_picker_message(items: List[dict], self_player_id: int) -> Tuple[str, types.InlineKeyboardMarkup]:
    candidates = [r for r in items if r["player_id"] != self_player_id]
    markup = types.InlineKeyboardMarkup()
    for r in candidates[:8]:
        markup.add(types.InlineKeyboardButton(
            f"{r['display_name']} ({round(r['elo'])})", callback_data=f"vs:{r['player_id']}",
        ))

    text = (
        "🆚 Выбери соперника для битвы статов:\n\n"
        "Или в любом чате напиши <code>@имя_бота Игрок1 vs Игрок2</code>, "
        "чтобы сравнить любых двух игроков."
    )
    return text, markup


def build_vs_message(data: dict) -> Tuple[str, Optional[types.InlineKeyboardMarkup]]:
    a, b = data["player_a"], data["player_b"]
    sa, sb = data["stats_a"], data["stats_b"]
    name_a, name_b = a["display_name"], b["display_name"]

    lines: List[str] = [f"🆚 <b>{name_a}</b> vs <b>{name_b}</b>", ""]
    points_a = points_b = 0
    for label, key, fmt in _STATS:
        val_a, val_b = sa.get(key), sb.get(key)
        if val_a is None or val_b is None:
            continue
        line, pa, pb = _stat_line(label, val_a, val_b, fmt)
        lines.append(line)
        points_a += pa
        points_b += pb

    lines.append("")
    lines.append(f"Счёт: {points_a}:{points_b}")

    h2h = data.get("head_to_head")
    if h2h:
        lines.append(f"📜 Личные встречи: {h2h['wins']}-{h2h['draws']}-{h2h['losses']}")

    lines.append("")
    if points_a == points_b:
        verdict = random.choice(_TIE)
    else:
        winner, loser = (name_a, name_b) if points_a > points_b else (name_b, name_a)
        pool = _LANDSLIDE if abs(points_a - points_b) >= 3 else _CLOSE
        verdict = random.choice(pool).format(winner=winner, loser=loser)
    lines.append(verdict)

    return "\n".join(lines), None
