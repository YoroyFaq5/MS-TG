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


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.message_id = message_id
    c.id = call_id
    return c


def test_handle_tournament_detail_callback_not_found():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.tournaments import handle_tournament_detail_callback

    call = _fake_callback("tourn:999")
    with patch("bot.handlers.tournaments.get_tournament_detail", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_tournament_detail_callback(call)

    mock_edit.assert_not_called()
    assert "не найден" in mock_answer.call_args[0][1]


def test_handle_tournament_detail_callback_success():
    from bot.handlers.tournaments import handle_tournament_detail_callback

    data = {
        "tournament": {"id": 1, "name": "Test Cup", "status": "active", "type": "individual"},
        "participant_count": 10, "games_finished": 1, "games_total": 3,
        "active_stage": None, "player_ratings": [],
    }
    call = _fake_callback("tourn:1")
    with patch("bot.handlers.tournaments.get_tournament_detail", return_value=data), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_tournament_detail_callback(call)

    assert "Test Cup" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()
