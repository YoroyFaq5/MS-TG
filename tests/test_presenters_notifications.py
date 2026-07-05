from bot.presenters.notifications import (
    build_next_slot_message,
    build_achievement_granted_message,
    build_title_granted_message,
    build_item_bought_out_message,
    build_fantasy_result_message,
    build_fantasy_prize_message,
    build_gift_received_message,
    build_season_award_message,
    build_game_finished_message,
)


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


def test_build_achievement_granted_message():
    text = build_achievement_granted_message({"achievement_name": "First Win"})
    assert "First Win" in text


def test_build_title_granted_message():
    text = build_title_granted_message({"title_name": "Champion"})
    assert "Champion" in text


def test_build_item_bought_out_message():
    text = build_item_bought_out_message({
        "item_name": "Golden Frame", "buyer_name": "Bob", "offer_price": 1200.0, "payout": 960.0,
    })
    assert "Golden Frame" in text and "Bob" in text and "1200" in text and "960" in text


def test_build_fantasy_result_message():
    text = build_fantasy_result_message({"tournament_name": "Cup", "points": 12.5})
    assert "Cup" in text and "12.5" in text


def test_build_fantasy_prize_message():
    text = build_fantasy_prize_message({"tournament_name": "Cup", "place": 1, "amount": 70.0})
    assert "1 место" in text and "Cup" in text and "70" in text


def test_build_gift_received_message_with_note():
    text = build_gift_received_message({"sender_name": "Bob", "item_name": "Frame", "message": "gg"})
    assert "Bob" in text and "Frame" in text and "gg" in text


def test_build_gift_received_message_without_note():
    text = build_gift_received_message({"sender_name": "Bob", "item_name": "Frame", "message": None})
    assert "Bob" in text and "«»" not in text


def test_build_season_award_message():
    text = build_season_award_message({"season_name": "Сезон 1", "rank": 1, "amount": 500.0})
    assert "Сезон 1" in text and "#1" in text and "500" in text


def test_build_game_finished_message_won():
    text = build_game_finished_message({"won": True, "total_score": 1.5, "bonus_score": 0.5})
    assert "✅" in text and "1.5" in text and "+0.5" in text


def test_build_game_finished_message_lost_no_bonus():
    text = build_game_finished_message({"won": False, "total_score": 0.0, "bonus_score": 0.0})
    assert "❌" in text
    assert "бонус" not in text
