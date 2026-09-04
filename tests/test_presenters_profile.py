from bot.presenters.profile import (
    build_not_linked_message, build_welcome_back_message, build_profile_card,
)


def test_build_not_linked_message():
    text, markup = build_not_linked_message()
    assert "не привязан" in text
    # UX fix (CLAUDE_TASK_BOT_RU_GROUPS.md п.5.2): a real link button, not
    # just an instruction in plain text.
    buttons = [b for row in markup.keyboard for b in row]
    assert any(b.url and "/profile/" in b.url for b in buttons)


def test_build_welcome_back_message():
    text, markup = build_welcome_back_message("Alice")
    assert "Alice" in text
    assert "Сравнить игроков" in text


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
    assert "60%" in text
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
