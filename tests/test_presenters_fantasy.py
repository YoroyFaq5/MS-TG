from bot.presenters.fantasy import (
    build_my_draft_message, build_no_draft_message, build_available_message,
    build_leaderboard_message,
)


def test_build_my_draft_message_with_picks():
    draft = {
        "tournament_id": 3, "status": "open", "total_points": 12.5,
        "picks": [{"player_id": 9, "player_name": "Alice", "points_earned": 5.0}],
    }
    text, markup = build_my_draft_message(draft)
    assert "Alice" in text
    assert "12.5" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "funpick:3:9"


def test_build_my_draft_message_no_picks():
    draft = {"tournament_id": 3, "status": "open", "total_points": 0, "picks": []}
    text, _ = build_my_draft_message(draft)
    assert "нет пиков" in text


def test_build_no_draft_message():
    text, markup = build_no_draft_message(3)
    assert "#3" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "fantasy_create:3"


def test_build_available_message():
    players = [{"id": 5, "name": "Bob", "elo": 1000.4}]
    text, markup = build_available_message(players, 3)
    assert "Bob" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "fpick:3:5"


def test_build_available_message_empty():
    text, _ = build_available_message([], 3)
    assert "Никого не осталось" in text


def test_build_leaderboard_message():
    entries = [{"rank": 1, "display_name": "Drafter", "total_points": 10.0, "pick_count": 3}]
    text, _ = build_leaderboard_message(entries, 3)
    assert "Drafter" in text
    assert "#3" in text


def test_build_leaderboard_message_empty():
    text, _ = build_leaderboard_message([], 3)
    assert "Пока пусто" in text
