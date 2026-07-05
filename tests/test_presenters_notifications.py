from bot.presenters.notifications import build_next_slot_message


def test_build_next_slot_message_includes_all_fields():
    text = build_next_slot_message({
        "tournament_name": "Test Cup",
        "round_number": 2,
        "table_number": 1,
        "seat_number": 7,
    })
    assert "Test Cup" in text
    assert "Раунд 2" in text
    assert "стол №1" in text
    assert "7" in text


def test_build_next_slot_message_handles_missing_tournament_name():
    text = build_next_slot_message({"round_number": 1, "table_number": 1, "seat_number": 3})
    assert "турнире" in text
