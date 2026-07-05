from unittest.mock import MagicMock, patch


def _fake_inline_query(query="", telegram_id=111, query_id="abc"):
    q = MagicMock()
    q.query = query
    q.from_user.id = telegram_id
    q.id = query_id
    return q


def test_handle_inline_query_empty_query_returns_no_results():
    from bot.handlers.inline import handle_inline_query

    query = _fake_inline_query(query="   ")
    with patch("bot.handlers.inline.search_players") as mock_search, \
         patch("bot.telegram_bot.bot.answer_inline_query") as mock_answer:
        handle_inline_query(query)

    mock_search.assert_not_called()
    mock_answer.assert_called_once_with("abc", [], cache_time=1)


def test_handle_inline_query_returns_results():
    from bot.handlers.inline import handle_inline_query

    query = _fake_inline_query(query="Alice")
    players = [{"id": 1, "display_name": "Alice", "elo": 1200}]
    with patch("bot.handlers.inline.search_players", return_value=players) as mock_search, \
         patch("bot.telegram_bot.bot.answer_inline_query") as mock_answer:
        handle_inline_query(query)

    mock_search.assert_called_once()
    assert mock_search.call_args[0][1] == "Alice"
    call_args = mock_answer.call_args
    assert call_args[0][0] == "abc"
    assert len(call_args[0][1]) == 1
    assert call_args[0][1][0].title == "Alice"
    assert call_args.kwargs["cache_time"] == 1


def test_handle_inline_query_api_error_returns_no_results():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.inline import handle_inline_query

    query = _fake_inline_query(query="Alice")
    with patch("bot.handlers.inline.search_players", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.answer_inline_query") as mock_answer:
        handle_inline_query(query)

    mock_answer.assert_called_once_with("abc", [], cache_time=1)
