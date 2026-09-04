from bot.keyboards.nav import cb
from bot.presenters.account import (
    build_unlink_confirm_message, build_unlink_done_message, build_unlink_cancelled_message,
    build_account_status_message,
)


def test_build_unlink_confirm_message_has_two_buttons():
    text, markup = build_unlink_confirm_message()
    assert "Отвязать" in text
    buttons = [b for row in markup.keyboard for b in row]
    callback_data = {b.callback_data for b in buttons}
    assert callback_data == {cb("account", "unlink-yes"), cb("account", "unlink-no")}


def test_build_unlink_done_message():
    text, markup = build_unlink_done_message()
    assert "отвязан" in text
    assert markup is None


def test_build_unlink_cancelled_message():
    text, markup = build_unlink_cancelled_message()
    assert "Отменено" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("profile", "open") for b in buttons)


def test_build_account_status_message():
    text, markup = build_account_status_message("Alice")
    assert "Alice" in text
    buttons = [b for row in markup.keyboard for b in row]
    assert any(b.callback_data == cb("account", "unlink-confirm") for b in buttons)
