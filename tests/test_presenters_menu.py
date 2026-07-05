from telebot import types

from bot.presenters.menu import build_main_menu_markup, MENU_ROWS


def test_build_main_menu_markup_is_persistent_reply_keyboard():
    markup = build_main_menu_markup()

    assert isinstance(markup, types.ReplyKeyboardMarkup)
    assert markup.resize_keyboard is True


def test_build_main_menu_markup_contains_all_expected_buttons():
    markup = build_main_menu_markup()

    button_texts = {
        btn.text if hasattr(btn, "text") else btn["text"]
        for row in markup.keyboard for btn in row
    }
    expected = {label for row in MENU_ROWS for label in row}
    assert button_texts == expected
