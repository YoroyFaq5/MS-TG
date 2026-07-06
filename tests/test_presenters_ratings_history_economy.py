from bot.presenters.ratings import build_ratings_message
from bot.presenters.history import build_history_message
from bot.presenters.economy import build_balance_message
from bot.presenters.achievements import build_achievements_message, build_titles_message


def test_build_ratings_message():
    data = {
        "items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 10}],
        "page": 1, "total_pages": 2,
    }
    text, markup = build_ratings_message(data, "global")
    assert "Alice" in text and "60.0%" in text
    assert "1/2" in text
    assert markup is not None
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1 and "След" in buttons[0].text


def test_build_ratings_message_last_page_no_next_button():
    data = {
        "items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 10}],
        "page": 2, "total_pages": 2,
    }
    text, markup = build_ratings_message(data, "global")
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1 and "Пред" in buttons[0].text


def test_build_ratings_message_empty():
    data = {"items": [], "page": 1, "total_pages": 0}
    text, markup = build_ratings_message(data, "global")
    assert "Пока пусто" in text
    assert markup is None


def test_build_history_message():
    data = {
        "items": [{
            "slot": {"role": "sheriff", "total_score": 1.5, "is_pu": True},
            "game": {"played_at": "2026-06-21T12:00:00+00:00"},
            "won": True,
        }],
        "page": 1, "per_page": 10,
    }
    text, markup = build_history_message(data)
    assert "2026-06-21" in text
    assert "✅" in text
    assert "🎯" in text
    assert markup is None  # только 1 запись при per_page=10 — дальше страниц нет


def test_build_history_message_has_next_page_button_when_full_page():
    items = [{
        "slot": {"role": "civilian", "total_score": 1.0, "is_pu": False},
        "game": {"played_at": "2026-06-21T12:00:00+00:00"},
        "won": True,
    }] * 2
    data = {"items": items, "page": 1, "per_page": 2}
    text, markup = build_history_message(data)
    assert markup is not None
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1 and "След" in buttons[0].text


def test_build_history_message_empty():
    text, markup = build_history_message({"items": [], "page": 1, "per_page": 10})
    assert "пока нет" in text.lower()
    assert markup is None


def test_build_balance_message():
    history = [{"created_at": "2026-06-21T00:00:00+00:00", "amount": 25.0, "reason": "welcome bonus"}]
    text, markup = build_balance_message(100.0, history)
    assert "100.0" in text
    assert "+25.0" in text
    assert "welcome bonus" in text
    assert markup is None


def test_build_achievements_message():
    items = [
        {"id": 1, "name": "First Win", "description": "desc", "unlocked": True, "pinned": True},
        {"id": 2, "name": "Hidden", "description": "desc2", "unlocked": False, "pinned": False},
    ]
    text, markup = build_achievements_message(items)
    assert "1/2" in text
    assert "First Win" in text
    assert "📌" in text
    assert "Hidden" not in text  # not unlocked, shouldn't be listed
    buttons = [b for row in markup.keyboard for b in row]
    assert len(buttons) == 1
    assert buttons[0].callback_data == "ach:unpin:1"


def test_build_achievements_message_no_unlocked_has_no_markup():
    items = [{"id": 2, "name": "Hidden", "description": "d", "unlocked": False, "pinned": False}]
    text, markup = build_achievements_message(items)
    assert markup is None


def test_build_titles_message():
    items = [{"title": {"name": "Champion"}, "equipped": True, "revoked": False}]
    text, _ = build_titles_message(items)
    assert "Champion" in text
    assert "экипирован" in text
