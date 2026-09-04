from telebot import types

from bot.presenters.menu import build_main_menu_message, build_reply_keyboard, MAIN_SECTIONS
from bot.keyboards.nav import cb


def test_build_reply_keyboard_is_a_single_compact_button():
    """Spec: at most a compact persistent Reply Keyboard as a quick entry
    point — not a duplicate of the inline menu."""
    markup = build_reply_keyboard()
    assert isinstance(markup, types.ReplyKeyboardMarkup)
    assert markup.resize_keyboard is True
    buttons = [btn.text if hasattr(btn, "text") else btn["text"] for row in markup.keyboard for btn in row]
    assert buttons == ["🏠 Меню"]


def test_build_main_menu_message_is_inline_and_covers_all_sections():
    text, markup = build_main_menu_message()
    assert isinstance(markup, types.InlineKeyboardMarkup)
    assert "Главное меню" in text

    callback_data = {btn.callback_data for row in markup.keyboard for btn in row}
    expected = {cb("nav", "open", key) for key, _ in MAIN_SECTIONS}
    assert callback_data == expected


def test_main_menu_covers_the_nine_required_sections():
    keys = {key for key, _ in MAIN_SECTIONS}
    assert keys == {"profile", "rating", "tourn", "fantasy", "shop", "inv", "gift", "vs", "notif"}


def test_main_menu_callback_data_within_telegram_limit():
    for key, _ in MAIN_SECTIONS:
        data = cb("nav", "open", key)
        assert len(data.encode("utf-8")) <= 64
