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


# ── Season — full resolution ─────────────────────────────────────────────────

_SEASON_DETAIL_DATA = {
    "season": {"id": 12, "name": "Сезон 5 2026", "status": "active", "gg_weight": 0.1,
               "winner_name": None, "winner_score": None},
    "ratings": {"items": [], "page": 1, "total_pages": 1},
    "min_games_for_top5": 8,
}


def test_season_deep_link_resolves_via_season_detail():
    with patch("bot.api_client.endpoints.seasons.get_season_detail", return_value=_SEASON_DETAIL_DATA) as mock_get:
        result = resolve_deep_link("season12", telegram_id=1)
    mock_get.assert_called_once()
    assert mock_get.call_args[0][1] == 12
    assert result is not None
    assert "Сезон 5 2026" in result[0]


def test_deleted_season_falls_back_to_none():
    from bot.api_client.exceptions import ApiNotFound

    with patch("bot.api_client.endpoints.seasons.get_season_detail", side_effect=ApiNotFound("nf")):
        assert resolve_deep_link("season999999", telegram_id=1) is None


# ── Series-tournament evening — full resolution ─────────────────────────────

_EVENING_DATA = {
    "series_tournament": {"id": 9, "tournament_id": 3, "tournament": {"id": 3, "name": "Series Cup"}},
    "series": {"id": 10, "name": "Вечер 2", "games_count": 5, "status": "finished"},
    "leaderboard": [],
}


def test_evening_deep_link_resolves_via_series_shortcut_and_detail():
    shortcut = {"series_tournament_id": 9, "tournament_id": 3, "name": "Вечер 2"}
    with patch("bot.api_client.endpoints.series_tournaments.get_series_shortcut", return_value=shortcut) as mock_shortcut, \
         patch("bot.api_client.endpoints.series_tournaments.get_series_evening_detail", return_value=_EVENING_DATA) as mock_detail:
        result = resolve_deep_link("ev3_10", telegram_id=1)

    assert mock_shortcut.call_args[0][1] == 10
    assert mock_detail.call_args[0][1] == 9
    assert mock_detail.call_args[0][2] == 10
    assert result is not None
    assert "Вечер 2" in result[0]


def test_deleted_evening_falls_back_to_none():
    from bot.api_client.exceptions import ApiNotFound

    with patch("bot.api_client.endpoints.series_tournaments.get_series_shortcut", side_effect=ApiNotFound("nf")):
        assert resolve_deep_link("ev3_999999", telegram_id=1) is None


# ── Fantasy — paid and practice, tournament and series scope ───────────────

_TOURNAMENT_NAME_DATA = {"tournament": {"id": 3, "name": "Cup"}}


def test_fantasy_tournament_deep_link_resolves_with_existing_draft():
    draft = {"status": "open", "pick_count": 2, "total_points": 0.0}
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=_TOURNAMENT_NAME_DATA), \
         patch("bot.services.linking_service.resolve_player_id", return_value=42), \
         patch("bot.api_client.endpoints.fantasy.get_my_draft", return_value=draft) as mock_draft:
        result = resolve_deep_link("fd3", telegram_id=1)

    assert mock_draft.call_args[0][-1] is False  # is_practice=False
    assert result is not None
    assert "Cup" in result[0]
    assert "🎓 тренировочный" not in result[0]


def test_fantasy_tournament_deep_link_unlinked_player_skips_draft_lookup():
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=_TOURNAMENT_NAME_DATA), \
         patch("bot.services.linking_service.resolve_player_id", return_value=None), \
         patch("bot.api_client.endpoints.fantasy.get_my_draft") as mock_draft:
        result = resolve_deep_link("fd3", telegram_id=1)

    mock_draft.assert_not_called()
    assert result is not None
    assert "нет драфта" in result[0]


def test_fantasy_series_deep_link_resolves():
    draft = {"status": "locked", "pick_count": 5, "total_points": 12.5}
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=_TOURNAMENT_NAME_DATA), \
         patch("bot.services.linking_service.resolve_player_id", return_value=42), \
         patch("bot.api_client.endpoints.fantasy.get_my_draft", return_value=draft) as mock_draft:
        result = resolve_deep_link("fs3_10", telegram_id=1)

    assert mock_draft.call_args[0][2] == 3   # tournament_id
    assert mock_draft.call_args[0][3] == 10  # series_id
    assert mock_draft.call_args[0][-1] is False
    assert result is not None
    assert "вечер" in result[0]


def test_fantasy_tournament_practice_deep_link_resolves():
    draft = {"status": "open", "pick_count": 1, "total_points": 0.0}
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=_TOURNAMENT_NAME_DATA), \
         patch("bot.services.linking_service.resolve_player_id", return_value=42), \
         patch("bot.api_client.endpoints.fantasy.get_my_draft", return_value=draft) as mock_draft:
        result = resolve_deep_link("fdp3", telegram_id=1)

    assert mock_draft.call_args[0][-1] is True  # is_practice=True
    assert result is not None
    assert "🎓 тренировочный" in result[0]


def test_fantasy_series_practice_deep_link_resolves():
    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", return_value=_TOURNAMENT_NAME_DATA), \
         patch("bot.services.linking_service.resolve_player_id", return_value=None), \
         patch("bot.api_client.endpoints.fantasy.get_my_draft") as mock_draft:
        result = resolve_deep_link("fsp3_10", telegram_id=1)

    mock_draft.assert_not_called()  # unlinked — draft lookup skipped like any other scope
    assert result is not None
    assert "🎓 тренировочный" in result[0] and "вечер" in result[0]


def test_fantasy_practice_payload_shapes():
    from bot.deeplink import _PATTERNS

    assert _PATTERNS["fantasy_tournament_practice"].match("fdp3")
    assert not _PATTERNS["fantasy_tournament"].match("fdp3")  # no cross-match with the paid pattern
    m = _PATTERNS["fantasy_series_practice"].match("fsp3_10")
    assert m and m.groups() == ("3", "10")
    assert not _PATTERNS["fantasy_series"].match("fsp3_10")


def test_deleted_tournament_falls_back_to_none_for_fantasy_link():
    from bot.api_client.exceptions import ApiNotFound

    with patch("bot.api_client.endpoints.tournaments.get_tournament_detail", side_effect=ApiNotFound("nf")):
        assert resolve_deep_link("fd999999", telegram_id=1) is None
        assert resolve_deep_link("fdp999999", telegram_id=1) is None


# ── Shop hub and item ────────────────────────────────────────────────────────

def test_shop_hub_deep_link_resolves_without_network():
    result = resolve_deep_link("shop", telegram_id=1)
    assert result is not None
    assert "Магазин" in result[0]


def test_shop_item_deep_link_resolves():
    item = {
        "id": 42, "name": "Golden Frame", "rarity": "epic", "price": 500,
        "category": "profile_customization", "description": None, "is_active": True,
        "already_owned": False, "current_owner_id": None, "balance": 1000,
    }
    with patch("bot.api_client.endpoints.shop.get_item_detail", return_value=item) as mock_get:
        result = resolve_deep_link("item42", telegram_id=777)

    assert mock_get.call_args[0][1] == 42
    assert mock_get.call_args[0][2] == 777
    assert result is not None
    assert "Golden Frame" in result[0]


def test_deleted_shop_item_falls_back_to_none():
    from bot.api_client.exceptions import ApiNotFound

    with patch("bot.api_client.endpoints.shop.get_item_detail", side_effect=ApiNotFound("nf")):
        assert resolve_deep_link("item999999", telegram_id=1) is None


def test_shop_item_payload_shape_does_not_collide_with_other_prefixes():
    from bot.deeplink import _PATTERNS

    assert _PATTERNS["shop_item"].match("item42")
    assert not _PATTERNS["shop"].match("item42")
    assert not _PATTERNS["game"].match("item42")


# ── Payload length stays comfortably within Telegram's /start limit ────────

def test_new_payload_prefixes_stay_within_telegram_start_payload_limit():
    """Telegram's /start deep-link payload is capped at 64 characters —
    even with unrealistically large ids, every prefix here must stay well
    under that so a real link never gets silently truncated."""
    huge_id = 99_999_999
    payloads = [
        f"season{huge_id}", f"fdp{huge_id}", f"fsp{huge_id}_{huge_id}",
        f"item{huge_id}", "shop", f"ev{huge_id}_{huge_id}",
    ]
    for payload in payloads:
        assert len(payload.encode("utf-8")) <= 64, payload
