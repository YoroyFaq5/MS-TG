import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from telebot import types
from telebot.apihelper import ApiTelegramException

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.players import search_players, compare_players
from bot.presenters.players import build_inline_results
from bot.presenters.vs import build_vs_message

logger = logging.getLogger(__name__)

_VS_SPLIT = re.compile(r"\s+vs\s+", re.IGNORECASE)


def _safe_answer_inline_query(inline_query_id: str, results: list) -> None:
    """
    Telegram даёт боту жёсткий и короткий дедлайн на ответ на inline-запрос;
    если сайт в этот момент тормозит, ответ может не успеть и Telegram
    вернёт "query is too old" — на этом этапе пользователю уже ничем не
    поможешь, поэтому просто логируем и не даём этому уронить обработку
    апдейта.
    """
    try:
        bot.answer_inline_query(inline_query_id, results, cache_time=1)
    except ApiTelegramException:
        logger.warning("Inline query answer arrived too late for Telegram to accept it")


def _try_vs_query(query_text: str) -> Optional[types.InlineQueryResultArticle]:
    """
    "Игрок1 vs Игрок2" -> один результат с RPG-сравнением этих двух игроков
    (bot/presenters/vs.py). Возвращает None, если разделителя нет, кто-то
    из игроков не находится однозначно, или сайт не успевает ответить в
    срок (fast=True — короткий таймаут без ретраев, см. ApiClient) —
    тогда handle_inline_query падает обратно на обычный поиск по имени.
    """
    parts = _VS_SPLIT.split(query_text, maxsplit=1)
    if len(parts) != 2:
        return None
    name_a, name_b = parts[0].strip(), parts[1].strip()
    if not name_a or not name_b:
        return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(search_players, api_client, name_a, fast=True)
            future_b = pool.submit(search_players, api_client, name_b, fast=True)
            candidates_a, candidates_b = future_a.result(), future_b.result()
        if not candidates_a or not candidates_b:
            return None
        id_a, id_b = candidates_a[0]["id"], candidates_b[0]["id"]
        if id_a == id_b:
            return None

        data = compare_players(api_client, id_a, id_b, fast=True)
    except ApiError:
        logger.warning("vs-сравнение в инлайне не успело выполниться в срок")
        return None

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
        _safe_answer_inline_query(inline_query.id, [])
        return

    vs_result = _try_vs_query(query_text)
    if vs_result is not None:
        _safe_answer_inline_query(inline_query.id, [vs_result])
        return

    try:
        players = search_players(api_client, query_text, fast=True)
    except ApiError:
        logger.warning("Inline player search did not finish in time")
        _safe_answer_inline_query(inline_query.id, [])
        return

    results = build_inline_results(players)
    _safe_answer_inline_query(inline_query.id, results)
