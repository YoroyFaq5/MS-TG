from bot.presenters.fantasy import (
    scope_cb, build_fantasy_events_message, build_fantasy_hub_message, build_my_draft_message,
    build_cancel_confirm_message, build_available_message, build_leaderboard_message,
    build_history_message,
)
from bot.keyboards.nav import cb


def test_scope_cb_encodes_tournament_series_and_practice_as_trailing_ints():
    assert scope_cb("open", 3) == cb("fantasy", "open", 3, 0, 0)
    assert scope_cb("open", 3, 7) == cb("fantasy", "open", 3, 7, 0)
    assert scope_cb("open", 3, 7, True) == cb("fantasy", "open", 3, 7, 1)


def test_build_fantasy_events_message_marks_existing_drafts():
    data = {
        "tournaments": [{"tournament": {"id": 1, "name": "Cup"}, "my_draft_id": 5}],
        "series": [{"series": {"id": 10, "name": "Вечер 1"}, "tournament_id": 1, "my_draft_id": None}],
    }
    text, markup = build_fantasy_events_message(data)
    buttons = [b for row in markup.keyboard for b in row]
    labels = [b.text for b in buttons]
    assert any(l.startswith("✅") for l in labels)
    assert any(l.startswith("➕") for l in labels)
    assert any(b.callback_data == scope_cb("open", 1) for b in buttons)
    assert any(b.callback_data == scope_cb("open", 1, 10) for b in buttons)


def test_build_fantasy_events_message_empty():
    text, _ = build_fantasy_events_message({"tournaments": [], "series": []})
    assert "нет доступных" in text


def test_build_fantasy_hub_no_draft_shows_create_button():
    text, markup = build_fantasy_hub_message(3, 0, False, "Cup", None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert scope_cb("create", 3, 0, False) in all_cb
    assert scope_cb("my", 3, 0, False) not in all_cb


def test_build_fantasy_hub_with_draft_shows_my_draft_button():
    draft = {"status": "open", "pick_count": 2, "total_points": 4.0}
    text, markup = build_fantasy_hub_message(3, 0, False, "Cup", draft)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert scope_cb("my", 3, 0, False) in all_cb
    assert "open" in text


def test_build_fantasy_hub_practice_toggle_switches_mode():
    text, markup = build_fantasy_hub_message(3, 0, False, "Cup", None)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert scope_cb("open", 3, 0, True) in all_cb  # switch to practice

    text2, markup2 = build_fantasy_hub_message(3, 0, True, "Cup", None)
    all_cb2 = [b.callback_data for row in markup2.keyboard for b in row]
    assert scope_cb("open", 3, 0, False) in all_cb2  # switch back to paid
    assert "тренировочный" in text2.lower()


def test_build_my_draft_message_with_picks():
    draft = {
        "id": 42, "status": "open", "total_points": 12.5,
        "picks": [{"player_id": 9, "player_name": "Alice", "points_earned": 5.0}],
    }
    text, markup = build_my_draft_message(draft, 3, 0, False)
    assert "Alice" in text
    assert "12.5" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("fantasy", "unpick", 42, 9) in all_cb


def test_build_my_draft_message_no_picks():
    draft = {"id": 42, "status": "open", "total_points": 0, "picks": []}
    text, _ = build_my_draft_message(draft, 3, 0, False)
    assert "нет пиков" in text


def test_build_my_draft_message_escapes_player_name():
    draft = {"id": 42, "status": "open", "total_points": 0, "picks": [
        {"player_id": 1, "player_name": "<i>x</i>", "points_earned": 0},
    ]}
    text, _ = build_my_draft_message(draft, 3, 0, False)
    assert "<i>x</i>" not in text
    assert "&lt;i&gt;" in text


def test_build_cancel_confirm_message_has_yes_no():
    text, markup = build_cancel_confirm_message(3, 0, False)
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert scope_cb("cancel", 3, 0, False) in all_cb
    assert scope_cb("my", 3, 0, False) in all_cb


def test_build_available_message():
    players = [{"id": 5, "name": "Bob", "elo": 1000.4}]
    text, markup = build_available_message(players, 3, 0, False)
    assert "Bob" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("fantasy", "pickf", 3, 0, 0, 5) in all_cb


def test_build_available_message_empty():
    text, _ = build_available_message([], 3, 0, False)
    assert "Никого не осталось" in text


def test_build_leaderboard_message():
    entries = [{"rank": 1, "display_name": "Drafter", "total_points": 10.0, "pick_count": 3}]
    text, _ = build_leaderboard_message(entries, "Cup", 3, 0, False)
    assert "Drafter" in text
    assert "Cup" in text


def test_build_leaderboard_message_empty():
    text, _ = build_leaderboard_message([], "Cup", 3, 0, False)
    assert "Пока пусто" in text


def test_build_history_message_shows_scope_and_mode():
    data = {
        "items": [
            {"tournament_series_id": None, "is_practice": False, "status": "scored", "total_points": 5.0, "pick_count": 2},
            {"tournament_series_id": 9, "is_practice": True, "status": "open", "total_points": 0.0, "pick_count": 0},
        ],
        "page": 1, "per_page": 10, "total": 2, "total_pages": 1,
    }
    text, _ = build_history_message(data)
    assert "турнир" in text
    assert "вечер" in text


def test_history_pagination_first_middle_last_page():
    from bot.keyboards.nav import pagination_row

    first = pagination_row(cb("fantasy", "history"), 1, 3)
    middle = pagination_row(cb("fantasy", "history"), 2, 3)
    last = pagination_row(cb("fantasy", "history"), 3, 3)

    assert not any(b.text.startswith("◀") for b in first)
    assert any(b.text.startswith("▶") for b in first)

    assert any(b.text.startswith("◀") for b in middle)
    assert any(b.text.startswith("▶") for b in middle)

    assert any(b.text.startswith("◀") for b in last)
    assert not any(b.text.startswith("▶") for b in last)
