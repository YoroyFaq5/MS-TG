from unittest.mock import patch

from bot.deeplink import resolve_deep_link


def test_unrecognized_payload_returns_none():
    assert resolve_deep_link("garbage!!", telegram_id=1) is None


def test_empty_payload_returns_none():
    assert resolve_deep_link("", telegram_id=1) is None
    assert resolve_deep_link(None, telegram_id=1) is None


def test_game_deep_link_resolves_via_game_detail():
    game_data = {
        "game": {"id": 5, "played_at": "2026-06-21T12:00:00+00:00", "win_side": "city"},
        "slots": [], "tournament_id": None, "tournament_series_id": None, "series_id": None,
    }
    with patch("bot.api_client.endpoints.games.get_game_detail", return_value=game_data) as mock_get:
        result = resolve_deep_link("g5", telegram_id=1)
    mock_get.assert_called_once()
    assert mock_get.call_args[0][1] == 5
    assert result is not None
    text, markup = result
    assert "Игра #5" in text


def test_tournament_deep_link_resolves_plain_tournament():
    data = {
        "tournament": {"id": 3, "name": "Cup", "status": "active", "type": "individual"},
        "series_tournament_id": None,
        "participant_count": 0, "games_finished": 0, "games_total": 0,
        "active_stage": None, "can_view_standings": True, "player_ratings": [], "team_ratings": [],
    }
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=data):
        result = resolve_deep_link("t3", telegram_id=1)
    assert result is not None
    assert "Cup" in result[0]


def test_tournament_deep_link_redirects_to_series_when_wrapped():
    plain_data = {
        "tournament": {"id": 3, "name": "Cup", "status": "active", "type": "individual"},
        "series_tournament_id": 9,
        "participant_count": 0, "games_finished": 0, "games_total": 0,
        "active_stage": None, "can_view_standings": True, "player_ratings": [], "team_ratings": [],
    }
    series_data = {
        "series_tournament": {"id": 9, "tournament_id": 3, "tournament": {"id": 3, "name": "Series Cup"}},
        "series": [], "overall_leaderboard": [],
    }
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=plain_data), \
         patch("bot.api_client.endpoints.series_tournaments.get_series_tournament_detail", return_value=series_data):
        result = resolve_deep_link("t3", telegram_id=1)
    assert result is not None
    assert "Series Cup" in result[0]


def test_unknown_game_id_falls_back_to_none():
    from bot.api_client.exceptions import ApiNotFound

    with patch("bot.api_client.endpoints.games.get_game_detail", side_effect=ApiNotFound("nf")):
        assert resolve_deep_link("g999999", telegram_id=1) is None


def test_gift_deep_link_resolves_without_network():
    result = resolve_deep_link("gift", telegram_id=1)
    assert result is not None
    assert "Подарки" in result[0]


def test_season_deep_link_payload_shape():
    from bot.deeplink import _PATTERNS

    assert _PATTERNS["season"].match("season12")
    assert not _PATTERNS["season"].match("season")
    assert not _PATTERNS["season"].match("seasonabc")


def test_evening_deep_link_payload_shape():
    from bot.deeplink import _PATTERNS

    m = _PATTERNS["evening"].match("ev3_10")
    assert m and m.groups() == ("3", "10")
