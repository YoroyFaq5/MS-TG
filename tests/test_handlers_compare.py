from unittest.mock import MagicMock, patch


def _fake_message(telegram_id=111, chat_id=555, text="", chat_type="private"):
    m = MagicMock()
    m.from_user.id = telegram_id
    m.chat.id = chat_id
    m.chat.type = chat_type
    m.text = text
    return m


def test_handle_compare_missing_argument():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_compare_non_numeric_argument():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare abc")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_compare_not_linked():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare 5")
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_compare_success():
    from bot.handlers.compare import handle_compare

    compare_data = {
        "player_a": {"display_name": "Alice"},
        "player_b": {"display_name": "Bob"},
        "stats_a": {"elo": 1050, "win_rate": 60.0, "avg_score": 1.5, "total_games": 10},
        "stats_b": {"elo": 1000, "win_rate": 40.0, "avg_score": 1.0, "total_games": 8},
        "head_to_head": None,
    }
    message = _fake_message(text="/compare 5")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.compare.compare", return_value=compare_data), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    text = mock_send.call_args[0][1]
    assert "Alice" in text and "Bob" in text


def test_handle_compare_opponent_not_found():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare 999")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.compare.compare", side_effect=ApiNotFound("not found")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert "не найден" in mock_send.call_args[0][1]


# ── новая публичная форма "/compare <ник 1> | <ник 2>" ──────────────────────

_COMPARE_DATA = {
    "player_a": {"display_name": "Alice"}, "player_b": {"display_name": "Bob"},
    "stats_a": {"elo": 1050, "win_rate": 60.0, "avg_score": 1.5, "total_games": 10},
    "stats_b": {"elo": 1000, "win_rate": 40.0, "avg_score": 1.0, "total_games": 8},
    "head_to_head": None,
}


def test_handle_compare_by_name_works_in_group():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare Alice | Bob", chat_type="group")
    with patch("bot.handlers.compare.search_players", side_effect=[
             [{"id": 1, "display_name": "Alice", "elo": 1050}],
             [{"id": 2, "display_name": "Bob", "elo": 1000}],
         ]), \
         patch("bot.handlers.compare.compare_players", return_value=_COMPARE_DATA) as mock_compare, \
         patch("bot.handlers.compare.check_group_command_rate_limit", return_value=(True, False)), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert mock_compare.call_args.args[1:] == (1, 2)
    assert "Alice" in mock_send.call_args[0][1] and "Bob" in mock_send.call_args[0][1]


def test_handle_compare_by_name_missing_second_half():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare Alice |", chat_type="group")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_compare_by_name_player_not_found():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare Zzz | Bob", chat_type="group")
    with patch("bot.handlers.compare.search_players", return_value=[]), \
         patch("bot.handlers.compare.check_group_command_rate_limit", return_value=(True, False)), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    assert "Zzz" in mock_send.call_args[0][1] and "не найден" in mock_send.call_args[0][1]


def test_handle_compare_by_name_same_player_both_sides():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare Alice | Alice", chat_type="group")
    with patch("bot.handlers.compare.search_players", return_value=[{"id": 1, "display_name": "Alice", "elo": 1000}]), \
         patch("bot.handlers.compare.check_group_command_rate_limit", return_value=(True, False)), \
         patch("bot.handlers.compare.compare_players") as mock_compare, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    mock_compare.assert_not_called()
    assert "один и тот же" in mock_send.call_args[0][1]


def test_handle_compare_by_name_rate_limited_in_group():
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare Alice | Bob", chat_type="group")
    with patch("bot.handlers.compare.check_group_command_rate_limit", return_value=(False, True)), \
         patch("bot.handlers.compare.search_players") as mock_search, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    mock_search.assert_not_called()
    assert "⏳" in mock_send.call_args[0][1]


def test_handle_compare_legacy_id_form_rejected_in_group():
    """The old '/compare <id>' shortcut depends on the caller's own linked
    account — meaningless/unsafe to advertise in a group, so it now just
    shows the new usage hint there instead of trying to resolve anyone."""
    from bot.handlers.compare import handle_compare

    message = _fake_message(text="/compare 5", chat_type="group")
    with patch("bot.services.linking_service.resolve") as mock_resolve, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_compare(message)

    mock_resolve.assert_not_called()
    assert "Использование" in mock_send.call_args[0][1]
