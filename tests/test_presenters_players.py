from telebot import types

from bot.presenters.players import build_inline_results


def test_build_inline_results_empty():
    assert build_inline_results([]) == []


def test_build_inline_results_maps_each_player():
    players = [
        {"id": 1, "display_name": "Alice", "elo": 1234.6},
        {"id": 2, "display_name": "Bob", "elo": 999.4},
    ]

    results = build_inline_results(players)

    assert len(results) == 2
    assert all(isinstance(r, types.InlineQueryResultArticle) for r in results)
    assert results[0].id == "1"
    assert results[0].title == "Alice"
    assert "1235" in results[0].description
    assert "Alice" in results[0].input_message_content.message_text
    assert "1235" in results[0].input_message_content.message_text
    assert results[1].id == "2"
    assert "999" in results[1].description
