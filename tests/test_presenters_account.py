from bot.presenters.account import (
    build_unlink_confirm_message, build_unlink_done_message, build_unlink_cancelled_message,
    build_account_status_message,
)


def test_build_unlink_confirm_message_has_two_buttons():
    text, markup = build_unlink_confirm_message()
    assert "Отвязать" in text
    buttons = [b for row in markup.keyboard for b in row]
    callback_data = {b.callback_data for b in buttons}
    assert callback_data == {"unlink_confirm", "unlink_cancel"}


def test_build_unlink_done_message():
    text, markup = build_unlink_done_message()
    assert "отвязан" in text
    assert markup is None


def test_build_unlink_cancelled_message():
    text, markup = build_unlink_cancelled_message()
    assert "Отменено" in text
    assert markup is None


def test_build_account_status_message():
    text, markup = build_account_status_message("Alice")
    assert "Alice" in text
    assert "/unlink" in text
    assert markup is None
