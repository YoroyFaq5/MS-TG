from unittest.mock import patch

import pytest

from bot.webhooks.events import dispatch


def test_dispatch_unknown_event_returns_false():
    assert dispatch("something-unknown", {}) is False


def test_dispatch_next_slot_sends_message_per_player():
    payload = {
        "players": [
            {"telegram_id": "111", "tournament_name": "Cup", "round_number": 1, "table_number": 1, "seat_number": 5},
            {"telegram_id": "222", "tournament_name": "Cup", "round_number": 1, "table_number": 2, "seat_number": 9},
        ]
    }
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        result = dispatch("next-slot", payload)
    assert result is True
    assert mock_send.call_count == 2
    sent_chat_ids = {call.args[0] for call in mock_send.call_args_list}
    assert sent_chat_ids == {111, 222}


def test_dispatch_next_slot_skips_players_without_telegram_id():
    payload = {"players": [{"tournament_name": "Cup", "round_number": 1, "table_number": 1, "seat_number": 5}]}
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        dispatch("next-slot", payload)
    mock_send.assert_not_called()


def test_dispatch_next_slot_continues_after_one_send_fails():
    payload = {
        "players": [
            {"telegram_id": "111", "round_number": 1, "table_number": 1, "seat_number": 1},
            {"telegram_id": "222", "round_number": 1, "table_number": 1, "seat_number": 2},
        ]
    }
    with patch("bot.telegram_bot.bot.send_message", side_effect=[Exception("boom"), None]) as mock_send:
        result = dispatch("next-slot", payload)
    assert result is True
    assert mock_send.call_count == 2


@pytest.mark.parametrize("event_type,payload", [
    ("achievement-granted", {"telegram_id": "111", "achievement_name": "First Win"}),
    ("title-granted", {"telegram_id": "111", "title_name": "Champion"}),
    ("item-bought-out", {"telegram_id": "111", "item_name": "Frame", "buyer_name": "Bob", "offer_price": 100.0, "payout": 80.0}),
    ("fantasy-result", {"telegram_id": "111", "tournament_name": "Cup", "points": 5.0}),
    ("fantasy-prize", {"telegram_id": "111", "tournament_name": "Cup", "place": 1, "amount": 70.0}),
    ("gift-received", {"telegram_id": "111", "item_name": "Frame", "sender_name": "Bob", "message": None}),
    ("season-award", {"telegram_id": "111", "season_name": "Season 1", "rank": 1, "amount": 500.0}),
    ("game-finished", {"telegram_id": "111", "won": True, "total_score": 1.0, "bonus_score": 0.0}),
])
def test_dispatch_simple_events_send_one_message(event_type, payload):
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        result = dispatch(event_type, payload)
    assert result is True
    mock_send.assert_called_once()
    assert mock_send.call_args[0][0] == 111


def test_dispatch_simple_event_skips_when_no_telegram_id():
    with patch("bot.telegram_bot.bot.send_message") as mock_send:
        result = dispatch("achievement-granted", {"achievement_name": "First Win"})
    assert result is True
    mock_send.assert_not_called()


def test_dispatch_simple_event_swallows_send_failure():
    with patch("bot.telegram_bot.bot.send_message", side_effect=Exception("boom")) as mock_send:
        result = dispatch("title-granted", {"telegram_id": "111", "title_name": "Champion"})
    assert result is True
    mock_send.assert_called_once()
