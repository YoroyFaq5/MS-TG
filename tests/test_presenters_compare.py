from bot.presenters.compare import build_compare_message


def test_build_compare_message_basic():
    data = {
        "player_a": {"display_name": "Alice"},
        "player_b": {"display_name": "Bob"},
        "stats_a": {"elo": 1050, "win_rate": 60.0, "avg_score": 1.5, "total_games": 10},
        "stats_b": {"elo": 1000, "win_rate": 40.0, "avg_score": 1.0, "total_games": 8},
        "head_to_head": None,
    }
    text, markup = build_compare_message(data)
    assert "Alice" in text and "Bob" in text
    assert "1050" in text and "1000" in text
    assert markup is None


def test_build_compare_message_with_head_to_head():
    data = {
        "player_a": {"display_name": "Alice"},
        "player_b": {"display_name": "Bob"},
        "stats_a": {"elo": 1050, "win_rate": 60.0, "avg_score": 1.5, "total_games": 10},
        "stats_b": {"elo": 1000, "win_rate": 40.0, "avg_score": 1.0, "total_games": 8},
        "head_to_head": {"wins": 3, "draws": 1, "losses": 2, "shared_games": 6},
    }
    text, _ = build_compare_message(data)
    assert "3-1-2" in text
