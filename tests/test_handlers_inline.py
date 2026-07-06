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


def test_handle_inline_query_vs_syntax_compares_two_players():
    from bot.handlers.inline import handle_inline_query

    compare_data = {
        "player_a": {"display_name": "Alice"},
        "player_b": {"display_name": "Bob"},
        "stats_a": {"avg_score": 1.5, "win_rate": 60.0, "total_games": 10, "elo": 1100, "pu_accuracy": None},
        "stats_b": {"avg_score": 1.0, "win_rate": 40.0, "total_games": 8, "elo": 1000, "pu_accuracy": None},
        "head_to_head": None,
    }
    query = _fake_inline_query(query="Alice vs Bob")
    with patch("bot.handlers.inline.search_players", side_effect=[
             [{"id": 1, "display_name": "Alice", "elo": 1100}],
             [{"id": 2, "display_name": "Bob", "elo": 1000}],
         ]), \
         patch("bot.handlers.inline.compare_players", return_value=compare_data) as mock_compare, \
         patch("bot.telegram_bot.bot.answer_inline_query") as mock_answer:
        handle_inline_query(query)

    mock_compare.assert_called_once()
    assert mock_compare.call_args[0][1:] == (1, 2)
    results = mock_answer.call_args[0][1]
    assert len(results) == 1
    assert "Alice" in results[0].title and "Bob" in results[0].title


def test_handle_inline_query_vs_syntax_falls_back_when_name_not_found():
    from bot.handlers.inline import handle_inline_query

    query = _fake_inline_query(query="Ghost vs Bob")
    players = [{"id": 2, "display_name": "Bob", "elo": 1000}]
    with patch("bot.handlers.inline.search_players", side_effect=[[], players, players]) as mock_search, \
         patch("bot.telegram_bot.bot.answer_inline_query") as mock_answer:
        handle_inline_query(query)

    # первый и второй вызов — попытка "vs"-разбора (обе стороны), третий — обычный
    # поиск по всей строке целиком, раз разбор не дал уверенного результата
    assert mock_search.call_count == 3
    assert mock_search.call_args[0][1] == "Ghost vs Bob"
    results = mock_answer.call_args[0][1]
    assert len(results) == 1
    assert results[0].title == "Bob"
