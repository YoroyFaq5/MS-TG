import logging
import re
from typing import Optional

from telebot import types

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.players import search_players, compare_players
from bot.presenters.players import build_inline_results
from bot.presenters.vs import build_vs_message

logger = logging.getLogger(__name__)

_VS_SPLIT = re.compile(r"\s+vs\s+", re.IGNORECASE)


def _try_vs_query(query_text: str) -> Optional[types.InlineQueryResultArticle]:
    """
    "Игрок1 vs Игрок2" -> один результат с RPG-сравнением этих двух игроков
    (bot/presenters/vs.py). Возвращает None, если разделителя нет или кто-то
    из игроков не находится однозначно — тогда handle_inline_query падает
    обратно на обычный поиск по имени, как и раньше.
    """
    parts = _VS_SPLIT.split(query_text, maxsplit=1)
    if len(parts) != 2:
        return None
    name_a, name_b = parts[0].strip(), parts[1].strip()
    if not name_a or not name_b:
        return None

    candidates_a = search_players(api_client, name_a)
    candidates_b = search_players(api_client, name_b)
    if not candidates_a or not candidates_b:
        return None
    id_a, id_b = candidates_a[0]["id"], candidates_b[0]["id"]
    if id_a == id_b:
        return None

    data = compare_players(api_client, id_a, id_b)
    text, _ = build_vs_message(data)
    title = f"🆚 {data['player_a']['display_name']} vs {data['player_b']['display_name']}"
    return types.InlineQueryResultArticle(
        id=f"vs-{id_a}-{id_b}",
        title=title,
        description="Тапни, чтобы отправить сравнение",
        input_message_content=types.InputTextMessageContent(text, parse_mode="HTML"),
    )


@bot.inline_handler(func=lambda query: True)
def handle_inline_query(inline_query) -> None:
    query_text = (inline_query.query or "").strip()
    if not query_text:
        bot.answer_inline_query(inline_query.id, [], cache_time=1)
        return

    try:
        vs_result = _try_vs_query(query_text)
        if vs_result is not None:
            bot.answer_inline_query(inline_query.id, [vs_result], cache_time=1)
            return
        players = search_players(api_client, query_text)
    except ApiError:
        logger.exception("Inline player search failed")
        bot.answer_inline_query(inline_query.id, [], cache_time=1)
        return

    results = build_inline_results(players)
    bot.answer_inline_query(inline_query.id, results, cache_time=1)
