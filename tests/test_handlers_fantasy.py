from unittest.mock import MagicMock, patch


def _fake_message(text=""):
    m = MagicMock()
    m.from_user.id = 111
    m.chat.id = 555
    m.text = text
    return m


def test_handle_fantasy_missing_argument():
    from bot.handlers.fantasy import handle_fantasy

    message = _fake_message(text="/fantasy")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_fantasy_not_linked():
    from bot.handlers.fantasy import handle_fantasy

    message = _fake_message(text="/fantasy 3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy(message)

    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_fantasy_no_draft_yet():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.fantasy import handle_fantasy

    message = _fake_message(text="/fantasy 3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_my_draft", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy(message)

    assert "fantasy_create 3" in mock_send.call_args[0][1]


def test_handle_fantasy_shows_draft():
    from bot.handlers.fantasy import handle_fantasy

    draft = {"tournament_id": 3, "status": "open", "total_points": 0, "picks": []}
    message = _fake_message(text="/fantasy 3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy(message)

    assert "Мой драфт" in mock_send.call_args[0][1]


def test_handle_fantasy_create_success():
    from bot.handlers.fantasy import handle_fantasy_create

    message = _fake_message(text="/fantasy_create 3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.create_draft") as mock_create, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy_create(message)

    mock_create.assert_called_once()
    assert "создан" in mock_send.call_args[0][1]


def test_handle_fantasy_create_business_error_shown_to_user():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.fantasy import handle_fantasy_create

    message = _fake_message(text="/fantasy_create 3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.create_draft", side_effect=ApiError("У вас уже есть драфт для этого турнира.")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy_create(message)

    assert "уже есть драфт" in mock_send.call_args[0][1]


def test_handle_fantasy_pick_missing_arguments():
    from bot.handlers.fantasy import handle_fantasy_pick

    message = _fake_message(text="/fantasy_pick 3")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy_pick(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_fantasy_pick_success():
    from bot.handlers.fantasy import handle_fantasy_pick

    draft = {"id": 42, "tournament_id": 3}
    message = _fake_message(text="/fantasy_pick 3 5")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.handlers.fantasy.add_pick") as mock_add_pick, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy_pick(message)

    mock_add_pick.assert_called_once_with(mock_add_pick.call_args[0][0], 111, 42, 5)
    assert "добавлен" in mock_send.call_args[0][1]


def test_handle_fantasy_available_success():
    from bot.handlers.fantasy import handle_fantasy_available

    players = [{"id": 5, "name": "Bob", "elo": 1000}]
    message = _fake_message(text="/fantasy_available 3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_available", return_value=players), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy_available(message)

    assert "Bob" in mock_send.call_args[0][1]


def test_handle_fantasy_leaderboard_success():
    from bot.handlers.fantasy import handle_fantasy_leaderboard

    entries = [{"rank": 1, "display_name": "Drafter", "total_points": 5.0, "pick_count": 2}]
    message = _fake_message(text="/fantasy_leaderboard 3")
    with patch("bot.handlers.fantasy.get_leaderboard", return_value=entries), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_fantasy_leaderboard(message)

    assert "Drafter" in mock_send.call_args[0][1]
