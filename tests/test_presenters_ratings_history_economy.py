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
    assert markup is None


def test_build_ratings_message_empty():
    data = {"items": [], "page": 1, "total_pages": 0}
    text, _ = build_ratings_message(data, "global")
    assert "Пока пусто" in text


def test_build_history_message():
    data = {
        "items": [{
            "slot": {"role": "sheriff", "total_score": 1.5, "is_pu": True},
            "game": {"played_at": "2026-06-21T12:00:00+00:00"},
            "won": True,
        }],
        "page": 1,
    }
    text, _ = build_history_message(data)
    assert "2026-06-21" in text
    assert "✅" in text
    assert "🎯" in text


def test_build_history_message_empty():
    text, _ = build_history_message({"items": [], "page": 1})
    assert "пока нет" in text.lower()


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
    text, _ = build_achievements_message(items)
    assert "1/2" in text
    assert "First Win" in text
    assert "📌" in text
    assert "Hidden" not in text  # not unlocked, shouldn't be listed


def test_build_titles_message():
    items = [{"title": {"name": "Champion"}, "equipped": True, "revoked": False}]
    text, _ = build_titles_message(items)
    assert "Champion" in text
    assert "экипирован" in text
