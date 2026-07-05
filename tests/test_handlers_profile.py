from unittest.mock import MagicMock, patch


def _fake_message(telegram_id=111, chat_id=555, text=""):
    m = MagicMock()
    m.from_user.id = telegram_id
    m.chat.id = chat_id
    m.text = text
    return m


def test_handle_me_not_linked():
    from bot.handlers.profile import handle_me

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_me(message)

    mock_send.assert_called_once()
    assert mock_send.call_args[0][0] == 555
    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_me_linked():
    from bot.handlers.profile import handle_me

    profile_data = {
        "player": {"display_name": "Alice", "elo": 1000},
        "elo": 1000, "global_rank": 1, "total_games": 5, "total_wins": 3,
        "win_rate": 60.0, "coins": 10.0, "equipped_title": None, "bio": None,
    }
    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.profile.get_profile", return_value=profile_data), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_me(message)

    text = mock_send.call_args[0][1]
    assert "Alice" in text


def test_handle_stats_not_linked():
    from bot.handlers.profile import handle_stats

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_stats(message)

    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_stats_api_error_gives_friendly_message():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.profile import handle_stats

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.profile.get_stats", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_stats(message)

    assert "не удалось" in mock_send.call_args[0][1].lower()
