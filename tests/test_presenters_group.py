"""
Presenters for the public group-chat commands (CLAUDE_TASK_BOT_RU_GROUPS.md,
раздел 3) — compact, non-paginated, never a callback into a private_only
handler for "see more" (a real URL/deep-link button instead, since a
forwarded group message must still work for anyone who taps it).
"""
from bot.presenters.group import (
    build_top_message, build_group_season_message, build_group_tournaments_message,
    build_group_player_card_message, build_player_disambiguation_message,
    build_player_not_found_message, build_group_compare_message, build_group_game_message,
    build_group_help_message, build_group_start_message, build_rate_limited_message,
    build_usage_error_message,
)


def test_build_top_message_lists_ranked_players():
    data = {"items": [
        {"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 10},
        {"rank": 2, "display_name": "Bob", "win_rate": 50.0, "games_played": 8},
    ]}
    text, markup = build_top_message(data, limit=10)
    assert "Alice" in text and "60%" in text and "10 игр" in text
    assert any(b.url for row in markup.keyboard for b in row)


def test_build_top_message_respects_limit():
    data = {"items": [{"rank": i, "display_name": f"P{i}", "win_rate": 50.0, "games_played": 1} for i in range(1, 11)]}
    text, _ = build_top_message(data, limit=3)
    assert "P4" not in text
    assert "P3" in text


def test_build_top_message_empty():
    text, _ = build_top_message({"items": []}, limit=10)
    assert "пусто" in text.lower()


def test_build_group_season_message_no_active_season():
    text, markup = build_group_season_message(None, [], 0)
    assert "нет активного сезона" in text.lower()


def test_build_group_season_message_with_top5():
    season = {"id": 3, "name": "Сезон 1", "status": "active", "starts_at": "2026-01-01T00:00:00+00:00", "ends_at": "2026-02-01T00:00:00+00:00"}
    top5 = [{"rank": 1, "display_name": "Alice", "season_rating": 12.5, "meets_top5_min_games": True}]
    text, markup = build_group_season_message(season, top5, 5)
    assert "Alice" in text and "12.5" in text
    assert any(b.url for row in markup.keyboard for b in row)


def test_build_group_tournaments_message_lists_and_links():
    tournaments = [{"id": 1, "name": "Cup A", "status": "active", "started_at": "2026-01-01T00:00:00+00:00"}]
    text, markup = build_group_tournaments_message(tournaments)
    assert "Cup A" in text
    assert markup.keyboard and markup.keyboard[0][0].url


def test_build_group_tournaments_message_empty():
    text, _ = build_group_tournaments_message([])
    assert "нет активных" in text.lower()


def test_build_group_player_card_message():
    player = {"display_name": "Alice", "rank": 3, "elo": 1050.4, "games_played": 20, "games_won": 12, "win_rate": 60.0}
    text, _ = build_group_player_card_message(player)
    assert "Alice" in text and "#3" in text and "60%" in text
    assert "1050" in text


def test_build_group_player_card_message_no_rank_yet():
    player = {"display_name": "New", "rank": None, "elo": 1000.0, "games_played": 0, "games_won": 0, "win_rate": 0.0}
    text, _ = build_group_player_card_message(player)
    assert "—" in text


def test_build_player_disambiguation_message_lists_candidates():
    candidates = [{"id": 1, "display_name": "Alice", "elo": 1000}, {"id": 2, "display_name": "Alice2", "elo": 1100}]
    text, markup = build_player_disambiguation_message(candidates, "alice")
    assert "alice" in text.lower()
    assert len(markup.keyboard) == 2


def test_build_player_not_found_message():
    text = build_player_not_found_message("Zzz")
    assert "Zzz" in text and "не найден" in text


def test_build_group_compare_message_strips_private_footer():
    """Reuses build_vs_message's text but must NOT carry its private
    nav-footer markup (a "vs:hub" callback would be rejected in a group
    since that handler is private_only)."""
    data = {
        "player_a": {"display_name": "Alice"}, "player_b": {"display_name": "Bob"},
        "stats_a": {"elo": 1050, "win_rate": 60.0, "avg_score": 1.5, "total_games": 10},
        "stats_b": {"elo": 1000, "win_rate": 40.0, "avg_score": 1.0, "total_games": 8},
        "head_to_head": None,
    }
    text, markup = build_group_compare_message(data)
    assert "Alice" in text and "Bob" in text
    assert markup.keyboard == []


def test_build_group_compare_message_prepends_note():
    data = {
        "player_a": {"display_name": "Alice"}, "player_b": {"display_name": "Bob"},
        "stats_a": {"elo": 1050, "win_rate": 60.0, "avg_score": 1.5, "total_games": 10},
        "stats_b": {"elo": 1000, "win_rate": 40.0, "avg_score": 1.0, "total_games": 8},
        "head_to_head": None,
    }
    text, _ = build_group_compare_message(data, resolved_note="Нашлось несколько игроков")
    assert text.startswith("Нашлось несколько игроков")


def test_build_group_game_message():
    data = {
        "game": {"id": 42, "played_at": "2026-01-01T20:00:00+00:00", "win_side": "mafia"},
        "slots": [
            {"seat_number": 1, "player_id": 1, "player_name": "Alice", "role": "don", "total_score": 2.5},
            {"seat_number": 2, "player_id": 2, "player_name": "Bob", "role": "sheriff", "total_score": 1.0},
        ],
    }
    text, markup = build_group_game_message(data)
    assert "42" in text and "Alice" in text and "Bob" in text
    assert markup.keyboard and markup.keyboard[0][0].url


def test_build_group_help_message_lists_public_commands():
    text, markup = build_group_help_message()
    for command in ("/top", "/season", "/tournaments", "/player", "/compare", "/game", "/help"):
        assert command in text
    assert markup.keyboard[0][0].url


def test_build_group_start_message_has_open_bot_button():
    text, markup = build_group_start_message()
    assert markup.keyboard[0][0].url


def test_build_rate_limited_message():
    assert "⏳" in build_rate_limited_message()


def test_build_usage_error_message():
    text = build_usage_error_message("/player &lt;ник&gt;")
    assert "Использование" in text and "/player" in text
