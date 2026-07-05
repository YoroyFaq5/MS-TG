from bot.presenters.stats import build_stats_message


def _base_stats(**overrides):
    stats = {
        "display_name": "Alice",
        "total_games": 10,
        "total_wins": 6,
        "win_rate": 60.0,
        "avg_score": 1.5,
        "best_score": 3.0,
        "worst_score": -1.0,
        "current_streak_signed": 2,
        "longest_streak": 4,
        "longest_loss_streak": 2,
        "pu_count": 3,
        "pu_sheriff_count": 1,
        "pu_accuracy": 66.7,
        "best_day_wins": {"date": "2026-06-21", "wins": 2, "games": 2},
        "best_day_bonus": {"date": "2026-06-21", "bonus": 6.0},
    }
    stats.update(overrides)
    return stats


def test_build_stats_message_includes_core_fields():
    data = {"stats": _base_stats(), "comparison_stats": None}
    text, markup = build_stats_message(data)
    assert "Alice" in text
    assert "60.0%" in text
    assert "Точность ЛХ: 66.7%" in text
    assert "2026-06-21" in text
    assert markup is None


def test_build_stats_message_without_pu_accuracy():
    data = {"stats": _base_stats(pu_accuracy=None, best_day_wins=None, best_day_bonus=None), "comparison_stats": None}
    text, _ = build_stats_message(data)
    assert "Точность ЛХ" not in text
    assert "Лучший день" not in text


def test_build_stats_message_with_comparison():
    data = {
        "stats": _base_stats(),
        "comparison_stats": {
            "rank": 2, "total_ranked_players": 10, "elo": 1050, "club_avg_elo": 1000,
            "elo_percentile": 80.0, "win_rate": 60.0, "club_avg_win_rate": 50.0,
            "win_rate_percentile": 70.0,
        },
    }
    text, _ = build_stats_message(data)
    assert "#2 из 10" in text
    assert "80.0%" in text
