"""
Handler-level coverage for the seasons / "Стол года" screens — button
navigation only (no network, no real Telegram): entering the hub from the
main menu, current season, "Моё место", rating pagination, back/home
footers, an unlinked account, an empty season, API errors, a player below
the top-5 games floor, and a stale (deleted) season id in callback_data.
"""
from unittest.mock import MagicMock, patch

from bot.api_client.exceptions import ApiError, ApiNotFound
from bot.keyboards.nav import cb


def _fake_callback(data, telegram_id=111, chat_id=555, message_id=999, call_id=42):
    c = MagicMock()
    c.data = data
    c.from_user.id = telegram_id
    c.message.chat.id = chat_id
    c.message.message_id = message_id
    c.id = call_id
    return c


_SEASON = {
    "id": 7, "name": "Сезон 5 (Сен–Окт) 2026", "status": "active",
    "gg_weight": 0.1, "winner_name": None, "winner_score": None,
}

_SEASON_WITH_WINNER = {
    "id": 3, "name": "Сезон 4 2026", "status": "finished",
    "gg_weight": 0.2, "winner_name": "Alice", "winner_score": 42.5,
}


def _paginated_ratings(items, page=1, total_pages=1):
    return {
        "season": _SEASON,
        "ratings": {"items": items, "page": page, "total_pages": total_pages},
        "min_games_for_top5": 8,
    }


# ── 1. Entering the seasons/ratings hub from the main menu ─────────────────

def test_nav_open_rating_reaches_the_ratings_hub_with_season_entries():
    from bot.handlers.menu import handle_nav_open

    call = _fake_callback(cb("nav", "open", "rating"))
    with patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_nav_open(call)

    text, markup = mock_edit.call_args[0][0], mock_edit.call_args[1]["reply_markup"]
    assert "Рейтинги" in text
    buttons = [b for row in markup.keyboard for b in row]
    callback_data = {b.callback_data for b in buttons}
    assert cb("season", "current") in callback_data
    assert cb("season", "list") in callback_data
    assert cb("season", "myplace-current") in callback_data
    assert cb("season", "winners", 1) in callback_data
    mock_answer.assert_called_once_with(42)


# ── 2. Current season ────────────────────────────────────────────────────

def test_handle_season_current_shows_active_season():
    from bot.handlers.seasons import handle_season_current

    call = _fake_callback(cb("season", "current"))
    with patch("bot.handlers.seasons.get_current_season", return_value=_SEASON) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_current(call)

    mock_get.assert_called_once()
    assert "Сезон 5" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_season_current_shows_winner_when_finished():
    from bot.handlers.seasons import handle_season_current

    call = _fake_callback(cb("season", "current"))
    with patch("bot.handlers.seasons.get_current_season", return_value=_SEASON_WITH_WINNER), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_current(call)

    assert "Alice" in mock_edit.call_args[0][0]


# ── 7. Empty season (no active season / no games played yet) ───────────────

def test_handle_season_current_when_no_active_season():
    from bot.handlers.seasons import handle_season_current

    call = _fake_callback(cb("season", "current"))
    with patch("bot.handlers.seasons.get_current_season", return_value=None), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_current(call)

    assert "нет активного сезона" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_season_detail_empty_season_has_no_games_message():
    from bot.handlers.seasons import handle_season_detail

    data = _paginated_ratings([])
    call = _fake_callback(cb("season", "detail", 7, 1))
    with patch("bot.handlers.seasons.get_season_detail", return_value=data), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_detail(call)

    assert "ещё нет игр" in mock_edit.call_args[0][0]


# ── 4. Rating pagination inside a season table ──────────────────────────────

def test_handle_season_detail_parses_season_id_and_page():
    from bot.handlers.seasons import handle_season_detail

    data = _paginated_ratings(
        [{"rank": 1, "display_name": "Bob", "season_rating": 12.0, "games_played": 10, "meets_top5_min_games": True}],
        page=2, total_pages=3,
    )
    call = _fake_callback(cb("season", "detail", 7, 2))
    with patch("bot.handlers.seasons.get_season_detail", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_detail(call)

    assert mock_get.call_args.args[1] == 7
    assert mock_get.call_args.kwargs["page"] == 2
    text = mock_edit.call_args[0][0]
    assert "Bob" in text and "2/3" in text
    markup = mock_edit.call_args[1]["reply_markup"]
    buttons = [b for row in markup.keyboard for b in row]
    callback_data = {b.callback_data for b in buttons}
    # Pagination row must offer both neighbouring pages for page 2 of 3.
    assert any(cd.startswith(cb("season", "detail", 7) + ":1") for cd in callback_data)
    assert any(cd.startswith(cb("season", "detail", 7) + ":3") for cd in callback_data)


def test_handle_season_winners_pagination():
    from bot.handlers.seasons import handle_season_winners

    data = {
        "items": [{"year": 2025, "number": 3, "winner_name": "Carl", "winner_score": 99.0}],
        "page": 1, "total_pages": 2,
    }
    call = _fake_callback(cb("season", "winners", 1))
    with patch("bot.handlers.seasons.get_season_winners", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_winners(call)

    assert mock_get.call_args.kwargs["page"] == 1
    assert "Carl" in mock_edit.call_args[0][0]


# ── 5. Back / home footer on every season screen ────────────────────────────

def test_season_current_has_back_to_hub_and_home():
    from bot.handlers.seasons import handle_season_current

    call = _fake_callback(cb("season", "current"))
    with patch("bot.handlers.seasons.get_current_season", return_value=_SEASON), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_current(call)

    markup = mock_edit.call_args[1]["reply_markup"]
    callback_data = {b.callback_data for row in markup.keyboard for b in row}
    assert cb("rating", "hub") in callback_data
    assert cb("nav", "home") in callback_data


def test_season_detail_has_back_to_hub_and_home():
    from bot.handlers.seasons import handle_season_detail

    data = _paginated_ratings([])
    call = _fake_callback(cb("season", "detail", 7, 1))
    with patch("bot.handlers.seasons.get_season_detail", return_value=data), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_detail(call)

    markup = mock_edit.call_args[1]["reply_markup"]
    callback_data = {b.callback_data for row in markup.keyboard for b in row}
    assert cb("rating", "hub") in callback_data
    assert cb("nav", "home") in callback_data


# ── 3 & 6. "Моё место" — linked and unlinked accounts ───────────────────────

def test_handle_season_myplace_linked_account():
    from bot.handlers.seasons import handle_season_myplace

    entry = {
        "rank": 4, "season_rating": 20.0, "games_played": 12, "games_won": 7,
        "win_rate_pct": 58.3, "gg_total": 3.0, "gg_weight": 0.1,
        "meets_top5_min_games": True,
    }
    data = {"season": _SEASON, "entry": entry, "min_games_for_top5": 8}
    call = _fake_callback(cb("season", "myplace", 7))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=42), \
         patch("bot.handlers.seasons.get_my_place", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_myplace(call)

    assert mock_get.call_args.args[1] == 111  # telegram_id from the callback's from_user
    assert mock_get.call_args.args[2] == 7
    assert "Место: <b>4</b>" in mock_edit.call_args[0][0]
    mock_answer.assert_called_once()


def test_handle_season_myplace_not_linked_shows_link_prompt_and_skips_api():
    from bot.handlers.seasons import handle_season_myplace

    call = _fake_callback(cb("season", "myplace", 7))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=None), \
         patch("bot.handlers.seasons.get_my_place") as mock_get_place, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_myplace(call)

    mock_get_place.assert_not_called()
    mock_answer.assert_called_once()
    assert mock_edit.called


def test_handle_season_myplace_current_not_linked_shows_link_prompt():
    from bot.handlers.seasons import handle_season_myplace_current

    call = _fake_callback(cb("season", "myplace-current"))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=None), \
         patch("bot.handlers.seasons.get_current_season") as mock_current, \
         patch("bot.telegram_bot.bot.edit_message_text"), \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_myplace_current(call)

    mock_current.assert_not_called()


def test_handle_season_myplace_current_resolves_active_season_first():
    from bot.handlers.seasons import handle_season_myplace_current

    entry = {
        "rank": 1, "season_rating": 50.0, "games_played": 15, "games_won": 10,
        "win_rate_pct": 66.7, "gg_total": 5.0, "gg_weight": 0.1,
        "meets_top5_min_games": True,
    }
    data = {"season": _SEASON, "entry": entry, "min_games_for_top5": 8}
    call = _fake_callback(cb("season", "myplace-current"))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=42), \
         patch("bot.handlers.seasons.get_current_season", return_value=_SEASON), \
         patch("bot.handlers.seasons.get_my_place", return_value=data) as mock_get, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_myplace_current(call)

    assert mock_get.call_args.args[2] == _SEASON["id"]
    assert "Место: <b>1</b>" in mock_edit.call_args[0][0]


def test_handle_season_myplace_current_when_no_active_season():
    from bot.handlers.seasons import handle_season_myplace_current

    call = _fake_callback(cb("season", "myplace-current"))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=42), \
         patch("bot.handlers.seasons.get_current_season", return_value=None), \
         patch("bot.handlers.seasons.get_my_place") as mock_get_place, \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_myplace_current(call)

    mock_get_place.assert_not_called()
    assert "нет активного сезона" in mock_edit.call_args[0][0]


# ── 9. Player below the top-5 games floor ───────────────────────────────────

def test_handle_season_myplace_below_top5_games_floor():
    from bot.handlers.seasons import handle_season_myplace

    entry = {
        "rank": 12, "season_rating": 5.0, "games_played": 3, "games_won": 1,
        "win_rate_pct": 33.3, "gg_total": 0.5, "gg_weight": 0.1,
        "meets_top5_min_games": False, "games_needed_for_top5": 5,
    }
    data = {"season": _SEASON, "entry": entry, "min_games_for_top5": 8}
    call = _fake_callback(cb("season", "myplace", 7))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=42), \
         patch("bot.handlers.seasons.get_my_place", return_value=data), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_myplace(call)

    text = mock_edit.call_args[0][0]
    assert "🔒" in text
    assert "Ещё 5" in text


def test_handle_season_myplace_no_games_played_yet():
    from bot.handlers.seasons import handle_season_myplace

    data = {"season": _SEASON, "entry": None, "min_games_for_top5": 8}
    call = _fake_callback(cb("season", "myplace", 7))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=42), \
         patch("bot.handlers.seasons.get_my_place", return_value=data), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query"):
        handle_season_myplace(call)

    assert "не сыграли рейтинговых игр" in mock_edit.call_args[0][0]


# ── 8. API errors — friendly toast, not a crash ─────────────────────────────

def test_handle_season_current_api_error_shows_friendly_toast_not_crash():
    """The callback is answered immediately (before the API call — see
    guarded_callback's answer_immediately), so an error afterward can no
    longer put its message in the answer toast; it falls back to a plain
    sent message instead (see dispatch.py::_report_failure)."""
    from bot.handlers.seasons import handle_season_current

    call = _fake_callback(cb("season", "current"))
    with patch("bot.handlers.seasons.get_current_season", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer, \
         patch("bot.telegram_bot.bot.send_message") as mock_send:
        handle_season_current(call)  # must not raise

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()
    assert "не удалось" in mock_send.call_args[0][1].lower()


def test_handle_season_detail_api_error_shows_friendly_toast_not_crash():
    from bot.handlers.seasons import handle_season_detail

    call = _fake_callback(cb("season", "detail", 7, 1))
    with patch("bot.handlers.seasons.get_season_detail", side_effect=ApiError("boom")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_detail(call)  # must not raise

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()


# ── 10. Stale callback (season deleted after the button was rendered) ──────

def test_handle_season_detail_stale_season_id_not_found():
    from bot.handlers.seasons import handle_season_detail

    call = _fake_callback(cb("season", "detail", 999999, 1))
    with patch("bot.handlers.seasons.get_season_detail", side_effect=ApiNotFound("not found")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_detail(call)  # must not raise

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()


def test_handle_season_myplace_stale_season_id_not_found():
    from bot.handlers.seasons import handle_season_myplace

    call = _fake_callback(cb("season", "myplace", 999999))
    with patch("bot.handlers.seasons.resolve_player_id", return_value=42), \
         patch("bot.handlers.seasons.get_my_place", side_effect=ApiNotFound("not found")), \
         patch("bot.telegram_bot.bot.edit_message_text") as mock_edit, \
         patch("bot.telegram_bot.bot.answer_callback_query") as mock_answer:
        handle_season_myplace(call)  # must not raise

    mock_edit.assert_not_called()
    mock_answer.assert_called_once()
