from unittest.mock import MagicMock, patch

from bot.keyboards.nav import cb


def _fake_message(chat_id=555, text="", from_id=111, chat_type="group"):
    m = MagicMock()
    m.from_user.id = from_id
    m.chat.id = chat_id
    m.chat.type = chat_type
    m.text = text
    return m


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42, chat_type="group"):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.chat.type = chat_type
    c.message.message_id = message_id
    c.id = call_id
    return c


# ── /top ──────────────────────────────────────────────────────────────────

def test_handle_top_defaults_to_10():
    from bot.handlers.group_commands import handle_top

    message = _fake_message(text="/top")
    data = {"items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 5}]}
    with patch("bot.handlers.group_commands.get_ratings", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_top(message)

    assert mock_get.call_args.kwargs["per_page"] == 10
    assert "Alice" in mock_send.call_args[0][1]


def test_handle_top_clamps_out_of_range_argument():
    from bot.handlers.group_commands import handle_top

    message = _fake_message(text="/top 99")
    with patch("bot.handlers.group_commands.get_ratings", return_value={"items": []}) as mock_get, \
         patch("bot.telegram_bot.bot.send_message"):
        handle_top(message)

    assert mock_get.call_args.kwargs["per_page"] == 10


def test_handle_top_rate_limited_in_group():
    from bot.handlers.group_commands import handle_top

    message = _fake_message(text="/top", chat_type="group")
    with patch("bot.handlers.group_commands.check_group_command_rate_limit", return_value=(False, True)), \
         patch("bot.handlers.group_commands.get_ratings") as mock_get, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_top(message)

    mock_get.assert_not_called()
    assert "⏳" in mock_send.call_args[0][1]


def test_handle_top_not_rate_limited_in_private():
    from bot.handlers.group_commands import handle_top

    message = _fake_message(text="/top", chat_type="private")
    with patch("bot.handlers.group_commands.check_group_command_rate_limit") as mock_limit, \
         patch("bot.handlers.group_commands.get_ratings", return_value={"items": []}), \
         patch("bot.telegram_bot.bot.send_message"):
        handle_top(message)

    mock_limit.assert_not_called()


# ── /season ───────────────────────────────────────────────────────────────

def test_handle_season_group_shows_compact_top5():
    from bot.handlers.group_commands import handle_season

    message = _fake_message(text="/season", chat_type="group")
    season = {"id": 3, "name": "Сезон 1", "status": "active", "starts_at": "2026-01-01T00:00:00+00:00", "ends_at": "2026-02-01T00:00:00+00:00"}
    detail = {"season": season, "min_games_for_top5": 5, "ratings": {"items": [
        {"rank": 1, "display_name": "Alice", "season_rating": 10.0, "meets_top5_min_games": True},
    ]}}
    with patch("bot.handlers.group_commands.get_current_season", return_value=season), \
         patch("bot.handlers.group_commands.get_season_detail", return_value=detail), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_season(message)

    assert "Alice" in mock_send.call_args[0][1]


def test_handle_season_group_no_active_season():
    from bot.handlers.group_commands import handle_season

    message = _fake_message(text="/season", chat_type="group")
    with patch("bot.handlers.group_commands.get_current_season", return_value=None), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_season(message)

    assert "нет активного сезона" in mock_send.call_args[0][1].lower()


def test_handle_season_private_uses_summary_presenter():
    from bot.handlers.group_commands import handle_season

    message = _fake_message(text="/season", chat_type="private")
    season = {"id": 3, "name": "Сезон 1", "status": "active"}
    with patch("bot.handlers.group_commands.get_current_season", return_value=season), \
         patch("bot.handlers.group_commands.build_season_summary_message", return_value=("text", None)) as mock_build, \
         patch("bot.telegram_bot.bot.send_message"):
        handle_season(message)

    mock_build.assert_called_once_with(season)


# ── /player ───────────────────────────────────────────────────────────────

def test_handle_player_missing_argument():
    from bot.handlers.group_commands import handle_player

    message = _fake_message(text="/player", chat_type="private")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_player(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_player_no_match():
    from bot.handlers.group_commands import handle_player

    message = _fake_message(text="/player Zzz", chat_type="private")
    with patch("bot.handlers.group_commands.search_players", return_value=[]), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_player(message)

    assert "не найден" in mock_send.call_args[0][1]


def test_handle_player_single_match_shows_card():
    from bot.handlers.group_commands import handle_player

    message = _fake_message(text="/player Alice", chat_type="private")
    card = {"display_name": "Alice", "rank": 1, "elo": 1000.0, "games_played": 5, "games_won": 3, "win_rate": 60.0}
    with patch("bot.handlers.group_commands.search_players", return_value=[{"id": 7, "display_name": "Alice", "elo": 1000}]), \
         patch("bot.handlers.group_commands.get_player", return_value=card), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_player(message)

    assert "Alice" in mock_send.call_args[0][1]


def test_handle_player_multiple_matches_shows_disambiguation():
    from bot.handlers.group_commands import handle_player

    message = _fake_message(text="/player Ali", chat_type="private")
    candidates = [{"id": 7, "display_name": "Alice", "elo": 1000}, {"id": 8, "display_name": "Alina", "elo": 900}]
    with patch("bot.handlers.group_commands.search_players", return_value=candidates), \
         patch("bot.handlers.group_commands.get_player") as mock_get_player, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_player(message)

    mock_get_player.assert_not_called()
    assert "несколько" in mock_send.call_args[0][1]


def test_handle_gplayer_show_callback_answers_immediately_and_sends_card():
    from bot.handlers.group_commands import handle_gplayer_show_callback

    call = _fake_callback(cb("gplayer", "show", 7), chat_type="group")
    card = {"display_name": "Alice", "rank": 1, "elo": 1000.0, "games_played": 5, "games_won": 3, "win_rate": 60.0}
    with patch("bot.handlers.group_commands.get_player", return_value=card), \
         patch("bot.telegram_bot.bot.send_message") as mock_send, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_gplayer_show_callback(call)

    mock_answer.assert_called_once_with(42)
    assert "Alice" in mock_send.call_args[0][1]


# ── /game ─────────────────────────────────────────────────────────────────

def test_handle_game_non_numeric_argument():
    from bot.handlers.group_commands import handle_game

    message = _fake_message(text="/game abc", chat_type="private")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_game(message)

    assert "Использование" in mock_send.call_args[0][1]


def test_handle_game_not_found():
    from bot.api_client.exceptions import ApiNotFound
    from bot.handlers.group_commands import handle_game

    message = _fake_message(text="/game 999", chat_type="private")
    with patch("bot.handlers.group_commands.get_game_detail", side_effect=ApiNotFound("nf")), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_game(message)

    assert "не найдена" in mock_send.call_args[0][1]


def test_handle_game_success():
    from bot.handlers.group_commands import handle_game

    message = _fake_message(text="/game 42", chat_type="private")
    data = {
        "game": {"id": 42, "played_at": "2026-01-01T20:00:00+00:00", "win_side": "city"},
        "slots": [{"seat_number": 1, "player_id": 1, "player_name": "Alice", "role": "civilian", "total_score": 1.0}],
    }
    with patch("bot.handlers.group_commands.get_game_detail", return_value=data), \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_game(message)

    assert "42" in mock_send.call_args[0][1] and "Alice" in mock_send.call_args[0][1]


# ── /help ─────────────────────────────────────────────────────────────────

def test_handle_help_in_group_shows_public_commands():
    from bot.handlers.group_commands import handle_help

    message = _fake_message(text="/help", chat_type="group")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_help(message)

    assert "/top" in mock_send.call_args[0][1]


def test_handle_help_in_private_shows_personal_commands():
    from bot.handlers.group_commands import handle_help

    message = _fake_message(text="/help", chat_type="private")
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_help(message)

    assert "/me" in mock_send.call_args[0][1]
