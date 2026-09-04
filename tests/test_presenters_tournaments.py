from bot.presenters.tournaments import (
    build_tournaments_list_message, build_tournament_detail_message,
    build_series_tournament_message, build_series_evening_message,
)
from bot.keyboards.nav import cb


def _paged(items, page=1, total_pages=1):
    return {"items": items, "page": page, "per_page": 8, "total": len(items), "total_pages": total_pages}


def test_build_tournaments_list_message():
    data = _paged([{"id": 1, "name": "Test Cup", "status": "active", "series_tournament_id": None}])
    text, markup = build_tournaments_list_message(data)
    assert "Test Cup" in text
    assert "#1" in text
    buttons = [b for row in markup.keyboard for b in row]
    open_buttons = [b for b in buttons if b.callback_data == cb("tourn", "open", 1, 0)]
    assert len(open_buttons) == 1


def test_build_tournaments_list_message_marks_series_tournaments():
    data = _paged([{"id": 2, "name": "Series Cup", "status": "pending", "series_tournament_id": 5}])
    text, markup = build_tournaments_list_message(data)
    assert "🔗" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("tourn", "open", 2, 5) for b in buttons)


def test_build_tournaments_list_message_empty():
    text, _ = build_tournaments_list_message(_paged([]))
    assert "пока нет" in text.lower()


def test_build_tournaments_list_message_has_status_filters_and_pagination():
    data = _paged([{"id": 1, "name": "Cup", "status": "active", "series_tournament_id": None}], page=2, total_pages=3)
    _, markup = build_tournaments_list_message(data, status="active")
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    # Status filter row (one button per STATUS_FILTERS entry, page reset to 1).
    assert cb("tourn", "list", "-", 1) in all_cb
    assert cb("tourn", "list", "active", 1) in all_cb
    assert cb("tourn", "list", "pending", 1) in all_cb
    assert cb("tourn", "list", "finished", 1) in all_cb
    # Pagination row for the current status, page 2/3.
    assert cb("tourn", "list", "active") + ":1" in all_cb
    assert cb("tourn", "list", "active") + ":3" in all_cb


def test_build_tournament_detail_message():
    data = {
        "tournament": {"id": 1, "name": "Test Cup", "status": "active", "type": "individual"},
        "participant_count": 10,
        "games_finished": 1,
        "games_total": 3,
        "active_stage": {"name": "Group"},
        "can_view_standings": True,
        "player_ratings": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0}],
        "team_ratings": [],
    }
    text, markup = build_tournament_detail_message(data)
    assert "Test Cup" in text
    assert "Group" in text
    assert "Alice" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("fantasy", "tourn", 1) in all_cb
    assert cb("nav", "home") in all_cb


def test_build_tournament_detail_message_hidden_standings():
    data = {
        "tournament": {"id": 1, "name": "Hidden Cup", "status": "active", "type": "individual"},
        "participant_count": 10, "games_finished": 1, "games_total": 3,
        "active_stage": None, "can_view_standings": False,
        "player_ratings": [], "team_ratings": [],
    }
    text, _ = build_tournament_detail_message(data)
    assert "скрыта" in text.lower()


def test_build_tournament_detail_message_escapes_name():
    data = {
        "tournament": {"id": 1, "name": "<b>Evil</b>", "status": "active", "type": "individual"},
        "participant_count": 0, "games_finished": 0, "games_total": 0,
        "active_stage": None, "can_view_standings": True, "player_ratings": [], "team_ratings": [],
    }
    text, _ = build_tournament_detail_message(data)
    assert "<b>Evil</b>" not in text
    assert "&lt;b&gt;" in text


def test_build_series_tournament_message():
    data = {
        "series_tournament": {"id": 5, "tournament_id": 2, "tournament": {"id": 2, "name": "Series Cup"}},
        "series": [{"id": 10, "name": "Вечер 1", "order": 1, "status": "active"}],
        "overall_leaderboard": [{"rank": 1, "display_name": "Bob", "total_score": 12.0, "series_played": 1}],
    }
    text, markup = build_series_tournament_message(data)
    assert "Series Cup" in text
    assert "Bob" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("tourn", "series-evening", 5, 10) in all_cb


def test_build_series_evening_message():
    data = {
        "series_tournament": {"id": 5, "tournament_id": 2, "tournament": {"name": "Series Cup"}},
        "series": {"id": 10, "name": "Вечер 1", "games_count": 3, "status": "finished"},
        "leaderboard": [{"rank": 1, "display_name": "Carl", "total_score": 5.0, "win_rate": 100.0}],
    }
    text, markup = build_series_evening_message(data)
    assert "Вечер 1" in text
    assert "Carl" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("fantasy", "series", 2, 10) in all_cb
    assert cb("tourn", "open", 2, 5) in all_cb
