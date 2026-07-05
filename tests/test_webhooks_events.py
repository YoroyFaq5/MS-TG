from unittest.mock import patch

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
