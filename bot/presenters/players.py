from typing import List

from telebot import types


def build_inline_results(players: list) -> List[types.InlineQueryResultArticle]:
    """
    Один результат на игрока — заголовок/описание для списка подсказок,
    input_message_content — то, что реально попадёт в чат при выборе.
    Намеренно не тянем полную карточку профиля (стата/ролe-аналитика) —
    инлайн-запрос должен ответить быстро на каждое нажатие клавиши,
    лишний вызов API на кандидата это не оправдывает.
    """
    results = []
    for p in players:
        elo = round(p["elo"])
        text = f"👤 <b>{p['display_name']}</b> — ELO {elo}"
        results.append(types.InlineQueryResultArticle(
            id=str(p["id"]),
            title=p["display_name"],
            description=f"ELO {elo}",
            input_message_content=types.InputTextMessageContent(text, parse_mode="HTML"),
        ))
    return results
