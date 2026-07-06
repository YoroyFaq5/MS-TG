from unittest.mock import MagicMock, patch


def _fake_message(text=""):
    m = MagicMock()
    m.from_user.id = 111
    m.chat.id = 555
    m.text = text
    return m


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.message_id = message_id
    c.id = call_id
    return c


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


def test_handle_fantasy_pick_callback_adds_pick():
    from bot.handlers.fantasy import handle_fantasy_pick_callback

    draft = {"id": 42, "tournament_id": 3}
    call = _fake_callback("fpick:3:5")
    with patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.handlers.fantasy.add_pick") as mock_add_pick, \
         patch("bot.handlers.fantasy.get_available", return_value=[]), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_pick_callback(call)

    mock_add_pick.assert_called_once_with(mock_add_pick.call_args[0][0], 111, 42, 5)
    mock_edit.assert_called_once()
    mock_answer.assert_called_once()


def test_handle_fantasy_unpick_callback_removes_pick():
    from bot.handlers.fantasy import handle_fantasy_pick_callback

    draft = {"id": 42, "tournament_id": 3, "status": "open", "total_points": 0, "picks": []}
    call = _fake_callback("funpick:3:5")
    with patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.handlers.fantasy.remove_pick") as mock_remove_pick, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_pick_callback(call)

    mock_remove_pick.assert_called_once_with(mock_remove_pick.call_args[0][0], 111, 42, 5)
    mock_edit.assert_called_once()
    mock_answer.assert_called_once()


def test_handle_fantasy_pick_callback_no_draft():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.fantasy import handle_fantasy_pick_callback

    call = _fake_callback("fpick:3:5")
    with patch("bot.handlers.fantasy.get_my_draft", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_pick_callback(call)

    assert "fantasy_create 3" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


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
