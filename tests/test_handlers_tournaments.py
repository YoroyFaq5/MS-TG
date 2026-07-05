from unittest.mock import MagicMock, patch


def _fake_message(chat_id=555, text=""):
    m = MagicMock()
    m.from_user.id = 111
    m.chat.id = chat_id
    m.text = text
    return m


def test_handle_tournaments_default():
    from bot.handlers.tournaments import handle_tournaments

    data = {"items": [{"id": 1, "name": "Test Cup", "status": "active"}]}
    message = _fake_message(text="/tournaments")
    with patch("bot.handlers.tournaments.get_tournaments", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_tournaments(message)

    assert mock_get.call_args.kwargs["status"] is None
    assert "Test Cup" in mock_send.call_args[0][1]


def test_handle_tournaments_with_status_filter():
    from bot.handlers.tournaments import handle_tournaments

    data = {"items": []}
    message = _fake_message(text="/tournaments finished")
    with patch("bot.handlers.tournaments.get_tournaments", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.send_message"):
        handle_tournaments(message)

    assert mock_get.call_args.kwargs["status"] == "finished"


def test_handle_tournament_detail_missing_argument():
    from bot.handlers.tournaments import handle_tournament_detail

    message = _fake_message(text="/tournament")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_tournament_detail(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_tournament_detail_not_found():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.tournaments import handle_tournament_detail

    message = _fake_message(text="/tournament 999")
    with patch("bot.handlers.tournaments.get_tournament_detail", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_tournament_detail(message)

    assert "не найден" in mock_send.call_args[0][1]


def test_handle_tournament_detail_success():
    from bot.handlers.tournaments import handle_tournament_detail

    data = {
        "tournament": {"name": "Test Cup", "status": "active", "type": "individual"},
        "participant_count": 10, "games_finished": 1, "games_total": 3,
        "active_stage": None, "player_ratings": [],
    }
    message = _fake_message(text="/tournament 1")
    with patch("bot.handlers.tournaments.get_tournament_detail", return_value=data), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_tournament_detail(message)

    assert "Test Cup" in mock_send.call_args[0][1]
