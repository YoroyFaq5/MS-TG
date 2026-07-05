from unittest.mock import MagicMock, patch


def _fake_message(telegram_id=111, chat_id=555, text=""):
    m = MagicMock()
    m.from_user.id = telegram_id
    m.chat.id = chat_id
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
