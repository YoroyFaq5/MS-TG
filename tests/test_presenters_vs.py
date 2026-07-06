from bot.presenters.vs import build_vs_message, build_vs_picker_message


def _compare_data(**overrides):
    data = {
        "player_a": {"display_name": "Alice"},
        "player_b": {"display_name": "Bob"},
        "stats_a": {"avg_score": 1.5, "win_rate": 60.0, "total_games": 10, "elo": 1100, "pu_accuracy": 80.0},
        "stats_b": {"avg_score": 1.0, "win_rate": 40.0, "total_games": 8, "elo": 1000, "pu_accuracy": 50.0},
        "head_to_head": None,
    }
    data.update(overrides)
    return data


def test_build_vs_message_landslide_winner_gets_trophies():
    text, markup = build_vs_message(_compare_data())
    assert "Alice" in text and "Bob" in text
    assert "Счёт: 5:0" in text
    assert markup is None


def test_build_vs_message_close_fight():
    data = _compare_data(stats_b={"avg_score": 1.6, "win_rate": 65.0, "total_games": 8, "elo": 1050, "pu_accuracy": 50.0})
    text, _ = build_vs_message(data)
    assert "Счёт: 3:2" in text


def test_build_vs_message_tie():
    same_stats = {"avg_score": 1.0, "win_rate": 50.0, "total_games": 10, "elo": 1000, "pu_accuracy": 50.0}
    data = _compare_data(stats_a=dict(same_stats), stats_b=dict(same_stats))
    text, _ = build_vs_message(data)
    assert "Счёт: 0:0" in text


def test_build_vs_message_skips_missing_stat():
    data = _compare_data(
        stats_a={"avg_score": 1.5, "win_rate": 60.0, "total_games": 10, "elo": 1100, "pu_accuracy": None},
        stats_b={"avg_score": 1.0, "win_rate": 40.0, "total_games": 8, "elo": 1000, "pu_accuracy": None},
    )
    text, _ = build_vs_message(data)
    assert "Меткость" not in text
    assert "Счёт: 4:0" in text


def test_build_vs_message_includes_head_to_head():
    data = _compare_data(head_to_head={"wins": 3, "draws": 1, "losses": 2})
    text, _ = build_vs_message(data)
    assert "3-1-2" in text


def test_build_vs_picker_message_excludes_self_and_builds_buttons():
    items = [
        {"player_id": 7, "display_name": "Me", "elo": 1000.0},
        {"player_id": 9, "display_name": "Rival", "elo": 1200.0},
    ]
    text, markup = build_vs_picker_message(items, self_player_id=7)
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "vs:9"
    assert "Rival" in buttons[0].text
