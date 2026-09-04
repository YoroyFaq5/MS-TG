from bot.presenters.ratings import build_ratings_message
from bot.presenters.history import build_history_message
from bot.presenters.economy import build_balance_message
from bot.presenters.achievements import build_achievements_message, build_titles_message
from bot.keyboards.nav import cb


def test_build_ratings_message():
    data = {
        "items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 10}],
        "page": 1, "total_pages": 2,
    }
    text, markup = build_ratings_message(data, "global")
    assert "Alice" in text and "60%" in text
    assert "1/2" in text
    all_buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("nav", "home") for b in all_buttons)  # always present
    assert any("▶️" in b.text for b in all_buttons)
    assert not any("◀️" in b.text for b in all_buttons)  # page 1 has no "previous"


def test_build_ratings_message_last_page_no_next_button():
    data = {
        "items": [{"rank": 1, "display_name": "Alice", "win_rate": 60.0, "games_played": 10}],
        "page": 2, "total_pages": 2,
    }
    _, markup = build_ratings_message(data, "global")
    all_buttons = [b for row in markup.keyboard for b in row]
    assert any("◀️" in b.text for b in all_buttons)
    assert not any("▶️" in b.text for b in all_buttons)


def test_build_ratings_message_empty_still_has_way_back():
    data = {"items": [], "page": 1, "total_pages": 0}
    text, markup = build_ratings_message(data, "global")
    assert "Пока пусто" in text
    assert markup is not None
    all_buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("nav", "home") for b in all_buttons)


def test_build_history_message():
    data = {
        "items": [{
            "slot": {"role": "sheriff", "total_score": 1.5, "is_pu": True},
            "game": {"id": 55, "played_at": "2026-06-21T12:00:00+00:00"},
            "won": True,
        }],
        "page": 1, "per_page": 10,
    }
    text, markup = build_history_message(data)
    assert "21.06.2026" in text  # русский формат даты
    assert "✅" in text
    assert "🎯" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert cb("game", "detail", 55) in all_cb
    assert cb("nav", "home") in all_cb


def test_build_history_message_has_next_page_button_when_full_page():
    items = [{
        "slot": {"role": "civilian", "total_score": 1.0, "is_pu": False},
        "game": {"id": 1, "played_at": "2026-06-21T12:00:00+00:00"},
        "won": True,
    }] * 2
    data = {"items": items, "page": 1, "per_page": 2}
    _, markup = build_history_message(data)
    all_buttons = [b for row in markup.keyboard for b in row]
    assert any("След" in b.text for b in all_buttons)


def test_build_history_message_empty_still_has_way_back():
    text, markup = build_history_message({"items": [], "page": 1, "per_page": 10})
    assert "пока нет" in text.lower()
    assert markup is not None


def test_build_balance_message():
    history = [{"created_at": "2026-06-21T00:00:00+00:00", "amount": 25.0, "reason": "welcome bonus"}]
    text, markup = build_balance_message(100.0, history)
    assert "100 монет" in text  # монеты — целыми, без ₽ и без 100.0
    assert "+25 монет" in text
    assert "welcome bonus" in text
    assert markup is not None


def test_build_balance_message_escapes_reason():
    text, _ = build_balance_message(0.0, [{"created_at": "2026-06-21", "amount": 1.0, "reason": "<b>x</b>"}])
    assert "<b>x</b>" not in text
    assert "&lt;b&gt;" in text


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
    all_buttons = [b for row in markup.keyboard for b in row]
    # Versioned callback_data (CLAUDE_TASK_BOT_RU_GROUPS.md п.5.3) — not the
    # old raw "ach:unpin:1" (still handled for backward compat, see
    # bot/handlers/achievements.py, but no longer emitted by the presenter).
    action_buttons = [b for b in all_buttons if b.callback_data == cb("ach", "unpin", 1)]
    assert len(action_buttons) == 1


def test_build_achievements_message_no_unlocked_still_has_way_back():
    items = [{"id": 2, "name": "Hidden", "description": "d", "unlocked": False, "pinned": False}]
    text, markup = build_achievements_message(items)
    assert markup is not None
    all_buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("nav", "home") for b in all_buttons)


def test_build_titles_message():
    items = [{"id": 9, "title": {"name": "Champion"}, "equipped": True, "revoked": False}]
    text, markup = build_titles_message(items)
    assert "Champion" in text
    assert "экипирован" in text
    all_cb = [b.callback_data for row in markup.keyboard for b in row]
    assert "v1:title:unequip" in all_cb
