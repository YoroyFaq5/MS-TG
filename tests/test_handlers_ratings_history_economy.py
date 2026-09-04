from unittest.mock import MagicMock, patch


def _fake_message(telegram_id=111, chat_id=555, text=""):
    m = MagicMock()
    m.from_user.id = telegram_id
    m.chat.id = chat_id
    m.text = text
    return m


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.chat.type = "private"
    c.message.message_id = message_id
    c.id = call_id
    return c


def test_handle_rating_default_page():
    from bot.handlers.ratings import handle_rating

    ratings_data = {"items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 5}],
                     "page": 1, "total_pages": 1}
    message = _fake_message(text="/rating")
    with patch("bot.handlers.ratings.get_ratings", return_value=ratings_data) as mock_get, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_rating(message)

    assert mock_get.call_args.kwargs["page"] == 1
    assert "Alice" in mock_send.call_args[0][1]


def test_handle_history_not_linked():
    from bot.handlers.history import handle_history

    message = _fake_message(text="/history")
    with patch("bot.services.linking_service.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_history(message)

    assert "не привязан" in mock_send.call_args[0][1]


def test_handle_history_with_page_arg():
    from bot.handlers.history import handle_history

    history_data = {"items": [], "page": 2, "per_page": 10}
    message = _fake_message(text="/history 2")
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.history.get_history", return_value=history_data) as mock_get, \
         patch("bot.telegram_bot.bot.send_message"):
        handle_history(message)

    assert mock_get.call_args.kwargs["page"] == 2


def test_handle_history_page_callback():
    from bot.handlers.history import handle_history_page_callback
    from bot.keyboards.nav import cb

    history_data = {"items": [{
        "slot": {"role": "civilian", "total_score": 1.0, "is_pu": False},
        "game": {"id": 1, "played_at": "2026-06-21T12:00:00+00:00"},
        "won": True,
    }], "page": 2, "per_page": 10, "total": 15, "total_pages": 2, "has_next": False}
    call = _fake_callback(cb("history", "list", 2))
    with patch("bot.handlers.history.resolve_player_id", return_value=7), \
         patch("bot.handlers.history.get_history", return_value=history_data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_history_page_callback(call)

    assert mock_get.call_args.kwargs["page"] == 2
    assert "2/2" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_rating_page_callback():
    from bot.handlers.ratings import handle_rating_page_callback
    from bot.keyboards.nav import cb

    ratings_data = {"items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 5}],
                     "page": 2, "total_pages": 2}
    call = _fake_callback(cb("rating", "global", 2))
    with patch("bot.handlers.ratings.get_ratings", return_value=ratings_data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_rating_page_callback(call)

    assert mock_get.call_args.kwargs["page"] == 2
    assert "Alice" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_balance_success():
    from bot.handlers.economy import handle_balance

    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.economy.get_balance", return_value={"balance": 42.0}), \
         patch("bot.handlers.economy.get_economy_history", return_value=[]), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_balance(message)

    assert "42 монеты" in mock_send.call_args[0][1]


def test_handle_achievements_success():
    from bot.handlers.achievements import handle_achievements

    items = [{"id": 1, "name": "First Win", "description": "d", "unlocked": True, "pinned": False}]
    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.achievements.get_achievements", return_value=items), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_achievements(message)

    assert "First Win" in mock_send.call_args[0][1]


def test_handle_achievement_toggle_callback_pin_versioned():
    from bot.handlers.achievements import handle_achievement_toggle_callback
    from bot.keyboards.nav import cb

    items = [{"id": 3, "name": "First Win", "description": "d", "unlocked": True, "pinned": True}]
    call = _fake_callback(cb("ach", "pin", 3))
    with patch("bot.handlers.achievements.pin") as mock_pin, \
         patch("bot.handlers.achievements.get_achievements", return_value=items), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_achievement_toggle_callback(call)

    mock_pin.assert_called_once_with(mock_pin.call_args[0][0], 111, 3)
    assert "First Win" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_achievement_toggle_callback_pin_legacy_unversioned_still_works():
    """Backward compat (CLAUDE_TASK_BOT_RU_GROUPS.md п.5.3): a button from
    a message sent before the v1: migration still carries the old raw
    'ach:pin:<id>' callback_data — it must keep working."""
    from bot.handlers.achievements import handle_achievement_toggle_callback

    items = [{"id": 3, "name": "First Win", "description": "d", "unlocked": True, "pinned": True}]
    call = _fake_callback("ach:pin:3")
    with patch("bot.handlers.achievements.pin") as mock_pin, \
         patch("bot.handlers.achievements.get_achievements", return_value=items), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_achievement_toggle_callback(call)

    mock_pin.assert_called_once_with(mock_pin.call_args[0][0], 111, 3)
    assert "First Win" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_achievement_toggle_callback_api_error():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.achievements import handle_achievement_toggle_callback
    from bot.keyboards.nav import cb

    call = _fake_callback(cb("ach", "unpin", 3))
    with patch("bot.handlers.achievements.unpin", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_achievement_toggle_callback(call)

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()


def test_handle_titles_success():
    from bot.handlers.achievements import handle_titles

    items = [{"id": 1, "title": {"name": "Champion"}, "equipped": False, "revoked": False}]
    message = _fake_message()
    with patch("bot.services.linking_service.resolve", return_value={"linked": True, "player_id": 7}), \
         patch("bot.handlers.achievements.get_titles", return_value=items), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_titles(message)

    assert "Champion" in mock_send.call_args[0][1]
