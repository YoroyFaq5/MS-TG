from bot.presenters.profile import (
    build_not_linked_message, build_welcome_back_message, build_profile_card,
)


def test_build_not_linked_message():
    text, markup = build_not_linked_message()
    assert "не привязан" in text
    assert markup is None


def test_build_welcome_back_message():
    text, markup = build_welcome_back_message("Alice")
    assert "Alice" in text
    assert "/me" in text


def test_build_profile_card_basic():
    data = {
        "player": {"display_name": "Alice", "elo": 1000},
        "elo": 1000,
        "global_rank": 3,
        "total_games": 10,
        "total_wins": 6,
        "win_rate": 60.0,
        "coins": 42.5,
        "equipped_title": None,
        "bio": None,
    }
    text, markup = build_profile_card(data)
    assert "Alice" in text
    assert "#3" in text
    assert "60.0%" in text
    assert markup is None


def test_build_profile_card_no_rank():
    data = {
        "player": {"display_name": "Bob", "elo": 1000},
        "elo": 1000,
        "global_rank": None,
        "total_games": 0,
        "total_wins": 0,
        "win_rate": 0.0,
        "coins": 0.0,
    }
    text, _ = build_profile_card(data)
    assert "—" in text
