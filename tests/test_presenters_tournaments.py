from bot.presenters.tournaments import build_tournaments_list_message, build_tournament_detail_message


def test_build_tournaments_list_message():
    data = {"items": [{"id": 1, "name": "Test Cup", "status": "active"}]}
    text, markup = build_tournaments_list_message(data)
    assert "Test Cup" in text
    assert "#1" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "tourn:1"


def test_build_tournaments_list_message_empty():
    text, _ = build_tournaments_list_message({"items": []})
    assert "пока нет" in text.lower()


def test_build_tournament_detail_message():
    data = {
        "tournament": {"name": "Test Cup", "status": "active", "type": "individual"},
        "participant_count": 10,
        "games_finished": 1,
        "games_total": 3,
        "active_stage": {"name": "Group"},
        "player_ratings": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0}],
    }
    text, markup = build_tournament_detail_message(data)
    assert "Test Cup" in text
    assert "Group" in text
    assert "Alice" in text
    assert markup is None


def test_build_tournament_detail_message_no_active_stage():
    data = {
        "tournament": {"name": "Finished Cup", "status": "finished", "type": "individual"},
        "participant_count": 8,
        "games_finished": 5,
        "games_total": 5,
        "active_stage": None,
        "player_ratings": [],
    }
    text, _ = build_tournament_detail_message(data)
    assert "Finished Cup" in text
    assert "Текущий этап" not in text
