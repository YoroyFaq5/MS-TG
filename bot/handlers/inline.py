import logging

from bot.telegram_bot import bot, api_client
from bot.api_client.exceptions import ApiError
from bot.api_client.endpoints.players import search_players
from bot.presenters.players import build_inline_results

logger = logging.getLogger(__name__)


@bot.inline_handler(func=lambda query: True)
def handle_inline_query(inline_query) -> None:
    query_text = (inline_query.query or "").strip()
    if not query_text:
        bot.answer_inline_query(inline_query.id, [], cache_time=1)
        return

    try:
        players = search_players(api_client, query_text)
    except ApiError:
        logger.exception("Inline player search failed")
        bot.answer_inline_query(inline_query.id, [], cache_time=1)
        return

    results = build_inline_results(players)
    bot.answer_inline_query(inline_query.id, results, cache_time=1)
