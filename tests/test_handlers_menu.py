from unittest.mock import MagicMock, patch


def _fake_message(telegram_id=111, chat_id=555, text=""):
    m = MagicMock()
    m.from_user.id = telegram_id
    m.chat.id = chat_id
    m.text = text
    return m


def test_menu_profile_delegates_to_handle_me():
    from bot.handlers.menu import menu_profile

    message = _fake_message(text="👤 Профиль")
    with patch("bot.handlers.menu.handle_me") as mock_handle:
        menu_profile(message)
    mock_handle.assert_called_once_with(message)


def test_menu_stats_delegates_to_handle_stats():
    from bot.handlers.menu import menu_stats

    message = _fake_message(text="📊 Статистика")
    with patch("bot.handlers.menu.handle_stats") as mock_handle:
        menu_stats(message)
    mock_handle.assert_called_once_with(message)


def test_menu_rating_delegates_to_handle_rating():
    from bot.handlers.menu import menu_rating

    message = _fake_message(text="🏆 Рейтинг")
    with patch("bot.handlers.menu.handle_rating") as mock_handle:
        menu_rating(message)
    mock_handle.assert_called_once_with(message)


def test_menu_history_delegates_to_handle_history():
    from bot.handlers.menu import menu_history

    message = _fake_message(text="📜 История")
    with patch("bot.handlers.menu.handle_history") as mock_handle:
        menu_history(message)
    mock_handle.assert_called_once_with(message)


def test_menu_balance_delegates_to_handle_balance():
    from bot.handlers.menu import menu_balance

    message = _fake_message(text="💰 Баланс")
    with patch("bot.handlers.menu.handle_balance") as mock_handle:
        menu_balance(message)
    mock_handle.assert_called_once_with(message)


def test_menu_achievements_delegates_to_handle_achievements():
    from bot.handlers.menu import menu_achievements

    message = _fake_message(text="🏅 Достижения")
    with patch("bot.handlers.menu.handle_achievements") as mock_handle:
        menu_achievements(message)
    mock_handle.assert_called_once_with(message)


def test_menu_tournaments_delegates_to_handle_tournaments():
    from bot.handlers.menu import menu_tournaments

    message = _fake_message(text="🎮 Турниры")
    with patch("bot.handlers.menu.handle_tournaments") as mock_handle:
        menu_tournaments(message)
    mock_handle.assert_called_once_with(message)


def test_menu_fantasy_sends_help_text():
    from bot.handlers.menu import menu_fantasy

    message = _fake_message(text="🎯 Fantasy")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        menu_fantasy(message)
    text = mock_send.call_args[0][1]
    assert "/fantasy" in text
    assert "Турниры" in text


def test_menu_account_not_linked():
    from bot.handlers.menu import menu_account

    message = _fake_message(text="⚙️ Аккаунт")
    with patch("bot.handlers.menu.resolve", return_value={"linked": False}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        menu_account(message)
    assert "не привязан" in mock_send.call_args[0][1]


def test_menu_account_linked():
    from bot.handlers.menu import menu_account

    message = _fake_message(text="⚙️ Аккаунт")
    with patch("bot.handlers.menu.resolve", return_value={"linked": True, "display_name": "Alice"}), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        menu_account(message)
    text = mock_send.call_args[0][1]
    assert "Alice" in text
    assert "/unlink" in text


def test_menu_account_api_error():
    from bot.api_client.exceptions import ApiError
    from bot.handlers.menu import menu_account

    message = _fake_message(text="⚙️ Аккаунт")
    with patch("bot.handlers.menu.resolve", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        menu_account(message)
    assert "не удалось" in mock_send.call_args[0][1].lower()
