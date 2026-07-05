from unittest.mock import MagicMock, patch


def _fake_message(telegram_id=111, chat_id=555):
    m = MagicMock()
    m.from_user.id = telegram_id
    m.chat.id = chat_id
    return m


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.message_id = message_id
    c.id = call_id
    return c


def test_handle_unlink_not_linked():
    from bot.handlers.account import handle_unlink

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_unlink(message)

    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_unlink_shows_confirmation():
    from bot.handlers.account import handle_unlink

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_unlink(message)

    text = mock_send.call_args[0][1]
    assert "Отвязать" in text
    markup = mock_send.call_args.kwargs["reply_markup"]
    assert markup is not None


def test_handle_unlink_callback_cancel():
    from bot.handlers.account import handle_unlink_callback

    call = _fake_callback("unlink_cancel")
    with patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_unlink_callback(call)

    assert "Отменено" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_unlink_callback_confirm():
    from bot.handlers.account import handle_unlink_callback

    call = _fake_callback("unlink_confirm")
    with patch("bot.handlers.account.unlink") as mock_unlink, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_unlink_callback(call)

    mock_unlink.assert_called_once_with(mock_unlink.call_args[0][0], 111)
    assert "отвязан" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_unlink_callback_confirm_api_error():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.account import handle_unlink_callback

    call = _fake_callback("unlink_confirm")
    with patch("bot.handlers.account.unlink", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_unlink_callback(call)

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()
    assert "не удалось" in mock_answer.call_args[0][1].lower()
