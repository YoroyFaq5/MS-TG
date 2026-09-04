from unittest.mock import MagicMock, patch

from bot.keyboards.nav import cb


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.message_id = message_id
    c.id = call_id
    return c


def test_handle_fantasy_events_lists_events():
    from bot.handlers.fantasy import handle_fantasy_events

    call = _fake_callback(cb("fantasy", "events"))
    data = {"tournaments": [], "series": []}
    with patch("bot.handlers.fantasy.get_events", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_events(call)

    mock_get.assert_called_once_with(mock_get.call_args[0][0], 111)
    mock_edit.assert_called_once()
    mock_answer.assert_called_once()


def test_handle_fantasy_open_not_linked_still_shows_hub():
    """Opening a Fantasy scope must work even when not linked (spec: browse
    without an account), just without a "my draft" state."""
    from bot.handlers.fantasy import handle_fantasy_open

    call = _fake_callback(cb("fantasy", "open", 3, 0, 0))
    with patch("bot.handlers.fantasy._scope_name", return_value="Cup"), \
         patch("bot.handlers.fantasy.resolve_player_id", return_value=None), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_open(call)

    assert "Cup" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_fantasy_create_success():
    from bot.handlers.fantasy import handle_fantasy_create

    call = _fake_callback(cb("fantasy", "create", 3, 0, 0))
    draft = {"id": 42, "status": "open", "total_points": 0, "picks": []}
    with patch("bot.handlers.fantasy.resolve_player_id", return_value=7), \
         patch("bot.handlers.fantasy.create_draft") as mock_create, \
         patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_create(call)

    mock_create.assert_called_once_with(mock_create.call_args[0][0], 111, 3, None, False)
    mock_edit.assert_called_once()
    assert "создан" in mock_answer.call_args[0][1]


def test_handle_fantasy_create_business_error_shows_alert():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.fantasy import handle_fantasy_create

    call = _fake_callback(cb("fantasy", "create", 3, 0, 0))
    with patch("bot.handlers.fantasy.resolve_player_id", return_value=7), \
         patch("bot.handlers.fantasy.create_draft", side_effect=ApiError("Уже есть драфт.")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_create(call)

    mock_edit.assert_not_called()
    assert "Уже есть драфт" in mock_answer.call_args[0][1]


def test_handle_fantasy_pick_from_available_adds_pick():
    from bot.handlers.fantasy import handle_fantasy_pick_from_available

    draft = {"id": 42}
    call = _fake_callback(cb("fantasy", "pickf", 3, 0, 0, 5))
    with patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.handlers.fantasy.add_pick") as mock_add, \
         patch("bot.handlers.fantasy.get_available", return_value=[]), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_pick_from_available(call)

    mock_add.assert_called_once_with(mock_add.call_args[0][0], 111, 42, 5)
    mock_edit.assert_called_once()
    assert "добавлен" in mock_answer.call_args[0][1]


def test_handle_fantasy_unpick_removes_and_shows_updated_draft():
    from bot.handlers.fantasy import handle_fantasy_unpick

    updated_draft = {
        "id": 42, "tournament_id": 3, "tournament_series_id": None, "is_practice": False,
        "status": "open", "total_points": 0, "picks": [],
    }
    call = _fake_callback(cb("fantasy", "unpick", 42, 5))
    with patch("bot.handlers.fantasy.remove_pick") as mock_remove, \
         patch("bot.handlers.fantasy.get_draft_by_id", return_value=updated_draft), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_unpick(call)

    mock_remove.assert_called_once_with(mock_remove.call_args[0][0], 111, 42, 5)
    mock_edit.assert_called_once()
    assert "убран" in mock_answer.call_args[0][1]


def test_handle_fantasy_cancel_confirm_screen():
    from bot.handlers.fantasy import handle_fantasy_cancel_confirm

    call = _fake_callback(cb("fantasy", "cancel-confirm", 3, 0, 0))
    with patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_cancel_confirm(call)

    assert "Точно отменить" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_fantasy_cancel_cancels_and_returns_to_hub():
    from bot.handlers.fantasy import handle_fantasy_cancel

    draft = {"id": 42}
    call = _fake_callback(cb("fantasy", "cancel", 3, 0, 0))
    with patch("bot.handlers.fantasy.get_my_draft", return_value=draft), \
         patch("bot.handlers.fantasy.cancel_draft") as mock_cancel, \
         patch("bot.handlers.fantasy._scope_name", return_value="Cup"), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_cancel(call)

    mock_cancel.assert_called_once_with(mock_cancel.call_args[0][0], 111, 42)
    assert "Cup" in mock_edit.call_args[0][0]
    assert "возвращены" in mock_answer.call_args[0][1]


def test_handle_fantasy_leaderboard():
    from bot.handlers.fantasy import handle_fantasy_leaderboard

    entries = [{"rank": 1, "display_name": "Drafter", "total_points": 5.0, "pick_count": 2}]
    call = _fake_callback(cb("fantasy", "lb", 3, 0, 0))
    with patch("bot.handlers.fantasy.get_leaderboard", return_value=entries), \
         patch("bot.handlers.fantasy._scope_name", return_value="Cup"), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_leaderboard(call)

    assert "Drafter" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_double_tap_on_create_is_rejected_by_lock():
    """Spec: a fast double-tap on a paid action (draft creation) must not
    run twice — guarded_callback's sensitive lock rejects the second call
    outright instead of invoking the handler body again."""
    from bot.handlers.fantasy import handle_fantasy_create
    from bot import storage

    call = _fake_callback(cb("fantasy", "create", 3, 0, 0))
    with patch("bot.storage.try_acquire_action_lock", return_value=False), \
         patch("bot.handlers.fantasy.create_draft") as mock_create, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_fantasy_create(call)

    mock_create.assert_not_called()
    mock_answer.assert_called_once()
