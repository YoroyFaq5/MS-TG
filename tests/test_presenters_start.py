from bot.presenters.start import build_welcome_message


def test_build_welcome_message_returns_text_and_no_markup():
    text, markup = build_welcome_message()
    assert "Мафия Style" in text
    assert markup is None
