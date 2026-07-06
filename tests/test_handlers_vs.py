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


def test_handle_vs_menu_not_linked():
    from bot.handlers.vs import handle_vs_menu

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_vs_menu(message)

    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_vs_menu_shows_candidates_excluding_self():
    from bot.handlers.vs import handle_vs_menu

    ratings_data = {"items": [
        {"player_id": 7, "display_name": "Me", "elo": 1000.0},
        {"player_id": 9, "display_name": "Rival", "elo": 1200.0},
    ]}
    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.vs.get_ratings", return_value=ratings_data), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_vs_menu(message)

    markup = mock_send.call_args.kwargs["reply_markup"]
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "vs:9"


def test_handle_vs_callback_success():
    from bot.handlers.vs import handle_vs_callback

    compare_data = {
        "player_a": {"display_name": "Alice"},
        "player_b": {"display_name": "Bob"},
        "stats_a": {"avg_score": 1.5, "win_rate": 60.0, "total_games": 10, "elo": 1100, "pu_accuracy": None},
        "stats_b": {"avg_score": 1.0, "win_rate": 40.0, "total_games": 8, "elo": 1000, "pu_accuracy": None},
        "head_to_head": None,
    }
    call = _fake_callback("vs:9")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.vs.compare", return_value=compare_data), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_vs_callback(call)

    text = mock_edit.call_args[0][0]
    assert "Alice" in text and "Bob" in text
    mock_answer.assert_called_once()


def test_handle_vs_callback_opponent_not_found():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.vs import handle_vs_callback

    call = _fake_callback("vs:999")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.vs.compare", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_vs_callback(call)

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()
