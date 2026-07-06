from unittest.mock import MagicMock, patch


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.message_id = message_id
    c.id = call_id
    return c


def test_handle_fantasy_my_callback_not_linked():
    from bot.handlers.fantasy import handle_fantasy_my_callback

    call = _fake_callback("fantasy_my:3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_my_callback(call)

    assert "не привязан" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_fantasy_my_callback_no_draft_yet():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.fantasy import handle_fantasy_my_callback

    call = _fake_callback("fantasy_my:3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_my_draft", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_my_callback(call)

    text = mock_edit.call_args[0][0]
    assert "нет драфта" in text
    markup = mock_edit.call_args.kwargs["reply_markup"]
    buttons = [b for row in markup.keyboard for b in row]
    assert buttons[0].callback_data == "fantasy_create:3"
    mock_answer.assert_called_once()


def test_handle_fantasy_my_callback_shows_draft():
    from bot.handlers.fantasy import handle_fantasy_my_callback

    draft = {"tournament_id": 3, "status": "open", "total_points": 0, "picks": []}
    call = _fake_callback("fantasy_my:3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_my_callback(call)

    assert "Мой драфт" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_fantasy_create_callback_success():
    from bot.handlers.fantasy import handle_fantasy_create_callback

    call = _fake_callback("fantasy_create:3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.create_draft") as mock_create, \
         patch("bot.handlers.fantasy.get_available", return_value=[]), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_create_callback(call)

    mock_create.assert_called_once()
    mock_edit.assert_called_once()
    assert "создан" in mock_answer.call_args[0][1]


def test_handle_fantasy_create_callback_business_error():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.fantasy import handle_fantasy_create_callback

    call = _fake_callback("fantasy_create:3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.create_draft",
               side_effect=ApiError("У вас уже есть драфт для этого турнира.")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_create_callback(call)

    mock_edit.assert_not_called()
    assert "уже есть драфт" in mock_answer.call_args[0][1]


def test_handle_fantasy_avail_callback_success():
    from bot.handlers.fantasy import handle_fantasy_avail_callback

    players = [{"id": 5, "name": "Bob", "elo": 1000}]
    call = _fake_callback("fantasy_avail:3")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.fantasy.get_available", return_value=players), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_avail_callback(call)

    assert "Bob" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


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

    assert "нет драфта" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_fantasy_lb_callback_success():
    from bot.handlers.fantasy import handle_fantasy_lb_callback

    entries = [{"rank": 1, "display_name": "Drafter", "total_points": 5.0, "pick_count": 2}]
    call = _fake_callback("fantasy_lb:3")
    with patch("bot.handlers.fantasy.get_leaderboard", return_value=entries), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_lb_callback(call)

    assert "Drafter" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()
